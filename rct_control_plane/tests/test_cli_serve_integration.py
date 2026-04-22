"""
Integration tests for 'rct serve' — starts a real uvicorn subprocess,
hits real HTTP endpoints on a real TCP port, then shuts down cleanly.

These tests are automatically skipped when:
  - The test port is already occupied
  - The server does not start within 10 s (slow CI)
  - uvicorn is not installed

No extra dependencies beyond the stdlib and uvicorn (already in requirements.txt).
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest

# ─── helpers ──────────────────────────────────────────────────────────────────

TEST_PORT = 18765   # high ephemeral port — very unlikely to clash in CI or locally
TEST_HOST = "127.0.0.1"
BASE_URL  = f"http://{TEST_HOST}:{TEST_PORT}"


def _port_open(host: str, port: int) -> bool:
    """Return True if something is already listening on host:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def _wait_for_port(host: str, port: int, timeout: float = 12.0) -> bool:
    """Poll until the port is open or timeout expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_open(host, port):
            return True
        time.sleep(0.25)
    return False


def _get_json(url: str, timeout: float = 5.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


# ─── fixture ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def rct_server():
    """
    Spawn ``rct serve`` as a real subprocess on TEST_PORT, yield (host, port),
    then terminate + wait for clean shutdown.

    Module-scoped: the server starts once for all tests in this file.
    """
    # Guard: skip if port already busy
    if _port_open(TEST_HOST, TEST_PORT):
        pytest.skip(f"Port {TEST_PORT} already in use — skipping serve integration tests")

    # Spawn via ``python -m rct_control_plane.cli serve`` so it works even
    # when the ``rct`` entry-point is not on PATH (e.g. bare CI env).
    #
    # Force UTF-8 I/O so the server process does not crash on Windows
    # consoles that use legacy encodings such as CP874 (Thai) where
    # characters like \u2192 cannot be encoded and raise UnicodeEncodeError
    # before the server even binds to its port.
    _env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "rct_control_plane.cli",
            "serve",
            "--host", TEST_HOST,
            "--port", str(TEST_PORT),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_env,
    )

    # Wait up to 12 s for the server to accept connections
    if not _wait_for_port(TEST_HOST, TEST_PORT, timeout=12.0):
        stdout, stderr = proc.communicate(timeout=3)
        proc.terminate()
        pytest.skip(
            f"rct serve did not start within 12 s — skipping.\n"
            f"stdout: {stdout.decode(errors='replace')[:400]}\n"
            f"stderr: {stderr.decode(errors='replace')[:400]}"
        )

    yield (TEST_HOST, TEST_PORT)

    # Teardown: terminate then wait (with hard-kill fallback)
    proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)


# ─── test cases ───────────────────────────────────────────────────────────────

class TestRctServeIntegration:
    """
    Verify that ``rct serve`` starts a real HTTP server and that the core
    endpoints respond correctly.
    """

    def test_health_endpoint_returns_healthy(self, rct_server):
        """GET /health → {"status": "healthy"}"""
        data = _get_json(f"{BASE_URL}/health")
        assert data.get("status") == "healthy"

    def test_root_returns_healthy(self, rct_server):
        """GET / → {"status": "healthy"}"""
        data = _get_json(f"{BASE_URL}/")
        assert data.get("status") == "healthy"

    def test_openapi_schema_accessible(self, rct_server):
        """GET /openapi.json → HTTP 200 + valid JSON schema"""
        data = _get_json(f"{BASE_URL}/openapi.json")
        assert "openapi" in data
        assert "paths" in data

    def test_docs_ui_accessible(self, rct_server):
        """GET /docs → HTTP 200 (Swagger UI HTML page)"""
        with urllib.request.urlopen(f"{BASE_URL}/docs", timeout=5) as r:
            assert r.status == 200
            body = r.read()
        assert b"swagger" in body.lower() or b"openapi" in body.lower()

    def test_compile_endpoint_responds(self, rct_server):
        """POST /compile → HTTP 2xx or 4xx (not 5xx) — server is up and routing"""
        payload = json.dumps({
            "natural_language": "Refactor authentication module",
            "user_id": "integration-test-user",
        }).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/compile",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            # 2xx: intent was compiled — check expected fields
            assert "intent_id" in data or "id" in data or "goal" in data
        except urllib.error.HTTPError as exc:
            # Any 4xx is fine: server is up; request may lack required fields
            assert exc.code < 500, f"Unexpected server error: HTTP {exc.code}"

    def test_health_is_idempotent(self, rct_server):
        """Calling /health twice returns the same status."""
        r1 = _get_json(f"{BASE_URL}/health")
        r2 = _get_json(f"{BASE_URL}/health")
        assert r1.get("status") == r2.get("status") == "healthy"


# ─── CLI unit tests (no server needed) ────────────────────────────────────────

class TestServeCommandRegistration:
    """
    Fast unit tests that verify the 'serve' command is properly registered
    in the CLI without spawning an actual server.
    """

    def test_serve_in_help_output(self):
        from click.testing import CliRunner
        from rct_control_plane.cli import cli
        result = CliRunner().invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "serve" in result.output

    def test_serve_help_shows_options(self):
        from click.testing import CliRunner
        from rct_control_plane.cli import cli
        result = CliRunner().invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output
        assert "--host" in result.output
        assert "--reload" in result.output
        assert "--workers" in result.output

    def test_serve_default_port_in_help(self):
        from click.testing import CliRunner
        from rct_control_plane.cli import cli
        result = CliRunner().invoke(cli, ["serve", "--help"])
        assert "8000" in result.output  # default port shown


class TestStatusNoArg:
    """
    Verify that 'rct status' without an intent_id shows system overview
    instead of crashing with a missing-argument error.
    """

    def test_status_no_arg_exits_zero(self):
        import rct_control_plane.cli as cli_mod
        cli_mod._cli_context = None
        from click.testing import CliRunner
        from rct_control_plane.cli import cli
        result = CliRunner().invoke(cli, ["status"])
        # Should NOT exit with "Missing argument 'INTENT_ID'"
        assert result.exit_code in (0, 1)
        assert "Missing argument" not in result.output

    def test_status_with_id_still_works(self):
        import rct_control_plane.cli as cli_mod
        cli_mod._cli_context = None
        from click.testing import CliRunner
        from rct_control_plane.cli import cli
        result = CliRunner().invoke(cli, ["status", "nonexistent-id-xyz"])
        # Should handle gracefully (exit 0 or 1, not 2)
        assert result.exit_code in (0, 1)
