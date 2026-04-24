"""
rct_control_plane/rich_formatter.py — Rich Terminal Output Formatters

Provides beautiful terminal output for all CLI commands using Rich library.
Replaces plain click.echo + manual table formatting with Rich components.

All functions accept data dicts and return rendered output via console.print().
When --output json is requested, these functions are bypassed entirely.

Reference: TUI-CLI RCT Design — Phase 4A
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.syntax import Syntax
from rich import box


# Shared console instance
_console: Optional[Console] = None


def get_console() -> Console:
    """Get or create the shared Rich console."""
    global _console
    if _console is None:
        _console = Console()
    return _console


def set_console(console: Console) -> None:
    """Override the shared console (for testing with StringIO)."""
    global _console
    _console = console


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "success": "bright_green",
    "completed": "bright_green",
    "active": "bright_green",
    "running": "bright_green",
    "healthy": "bright_green",
    "passed": "bright_green",
    "blocked": "bright_red",
    "error": "bright_red",
    "failed": "bright_red",
    "unhealthy": "bright_red",
    "warning": "yellow",
    "pending": "yellow",
    "unknown": "dim",
}


def _colorize_status(status: str) -> str:
    """Wrap status text in a Rich color tag."""
    color = _STATUS_COLORS.get(status.lower(), "white")
    return f"[{color}]{status}[/{color}]"


# ---------------------------------------------------------------------------
# Intent Table
# ---------------------------------------------------------------------------

def render_intent_table(intents: List[Dict[str, Any]]) -> None:
    """Render a list of intents as a Rich table."""
    console = get_console()
    table = Table(
        title="Intents",
        box=box.ROUNDED,
        border_style="bright_cyan",
        show_lines=True,
    )
    table.add_column("ID", style="bright_cyan", min_width=12)
    table.add_column("Type", style="white")
    table.add_column("Scope", style="white")
    table.add_column("Priority", style="bright_magenta")
    table.add_column("Valid", style="white")
    table.add_column("Created", style="dim")

    for intent in intents:
        valid = "✅" if intent.get("is_valid", True) else "❌"
        table.add_row(
            str(intent.get("intent_id", "—")),
            str(intent.get("intent_type", "—")),
            str(intent.get("scope", "—")),
            str(intent.get("priority", "—")),
            valid,
            str(intent.get("created_at", "—")),
        )

    console.print(table)


# ---------------------------------------------------------------------------
# State Panel
# ---------------------------------------------------------------------------

def render_state_panel(state: Dict[str, Any]) -> None:
    """Render intent state as a styled Rich panel."""
    console = get_console()

    status = state.get("phase", state.get("current_phase", "unknown"))
    status_display = _colorize_status(status)

    lines = [
        f"[bold]Intent ID:[/] {state.get('state_id', '—')}",
        f"[bold]Phase:[/] {status_display}",
        f"[bold]Created:[/] {state.get('created_at', '—')}",
        f"[bold]Updated:[/] {state.get('updated_at', '—')}",
    ]

    if "history" in state:
        lines.append(f"[bold]Transitions:[/] {len(state['history'])}")

    content = "\n".join(lines)
    console.print(Panel(
        content,
        title="[bold white]Intent State[/]",
        border_style="bright_cyan",
        padding=(1, 2),
    ))


# ---------------------------------------------------------------------------
# Audit Tree
# ---------------------------------------------------------------------------

def render_audit_tree(audit_data: Dict[str, Any]) -> None:
    """Render audit trail as a Rich tree with emoji nodes."""
    console = get_console()

    intent_id = audit_data.get("intent_id", "unknown")
    tree = Tree(f"🔍 [bold bright_cyan]Audit Trail — {intent_id}[/]")

    # Chain integrity
    integrity = audit_data.get("chain_integrity", {})
    integrity_node = tree.add("🔗 Chain Integrity")
    # Support both dict format and flat bool format
    if isinstance(integrity, dict):
        valid = integrity.get("is_valid", False)
    else:
        valid = audit_data.get("integrity_verified", False)
    color = "bright_green" if valid else "bright_red"
    integrity_node.add(f"Valid: [{color}]{valid}[/{color}]")
    if isinstance(integrity, dict):
        integrity_node.add(f"Entries: {integrity.get('total_entries', 0)}")
    else:
        integrity_node.add(f"Events: {audit_data.get('event_count', 0)}")

    # Events
    events = audit_data.get("events", [])
    if events:
        events_node = tree.add(f"📋 Events ({len(events)})")
        for event in events[-10:]:  # Show last 10
            ts = event.get("timestamp", "")
            action = event.get("action", event.get("event_type", "unknown"))
            data = event.get("data", {})
            success = data.get("success", True) if isinstance(data, dict) else True
            emoji = "✅" if success else "❌"
            events_node.add(f"{emoji} [{ts}] {action}")

    console.print(tree)


# ---------------------------------------------------------------------------
# Metrics Panel
# ---------------------------------------------------------------------------

def render_metrics_panel(metrics: Dict[str, Any]) -> None:
    """Render observer metrics as a 2-column table inside a panel."""
    console = get_console()

    table = Table(box=box.SIMPLE, show_header=True, border_style="bright_cyan")
    table.add_column("Metric", style="bright_cyan", min_width=25)
    table.add_column("Value", style="white", justify="right")

    def _flatten(data: Dict, prefix: str = "") -> None:
        for key, value in sorted(data.items()):
            full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
            if isinstance(value, dict):
                _flatten(value, full_key)
            else:
                table.add_row(full_key, str(value))

    _flatten(metrics)

    console.print(Panel(
        table,
        title="[bold white]Observer Metrics[/]",
        border_style="bright_magenta",
        padding=(0, 1),
    ))


# ---------------------------------------------------------------------------
# Adapter Status Table
# ---------------------------------------------------------------------------

def render_adapter_status(adapters: List[Dict[str, Any]]) -> None:
    """Render adapter health status as a Rich table."""
    console = get_console()

    table = Table(
        title="Adapter Status",
        box=box.ROUNDED,
        border_style="bright_cyan",
        show_lines=True,
    )
    table.add_column("Adapter", style="bold white", min_width=20)
    table.add_column("Version", style="dim")
    table.add_column("Security", style="bright_magenta")
    table.add_column("Health", min_width=8)
    table.add_column("Actions", style="dim")
    table.add_column("Latency", justify="right")

    for adapter in adapters:
        health = adapter.get("healthy", False)
        health_display = "[bright_green]● ONLINE[/]" if health else "[bright_red]● OFFLINE[/]"
        actions = ", ".join(adapter.get("supported_actions", [])[:5])
        if len(adapter.get("supported_actions", [])) > 5:
            actions += "..."
        latency_val = adapter.get("avg_latency_ms", adapter.get("latency_ms"))
        latency_str = f"{latency_val:.1f}ms" if latency_val is not None else "—"

        table.add_row(
            adapter.get("name", adapter.get("adapter_name", "—")),
            adapter.get("version", "—"),
            adapter.get("security_level", "—"),
            health_display,
            actions,
            latency_str,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Governance Violations Table
# ---------------------------------------------------------------------------

def render_governance_violations(violations: List[Dict[str, Any]]) -> None:
    """Render governance violations as a red-bordered table."""
    console = get_console()

    if not violations:
        console.print(Panel(
            "[bright_green]No governance violations recorded.[/]",
            title="[bold white]Governance Log[/]",
            border_style="bright_green",
        ))
        return

    table = Table(
        title=f"⚠️  Governance Violations ({len(violations)})",
        box=box.HEAVY,
        border_style="bright_red",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Rule / Packet", style="bright_red")
    table.add_column("Severity / Action", style="white")
    table.add_column("Description", style="yellow", max_width=50)
    table.add_column("Timestamp", style="dim")

    for idx, v in enumerate(violations, 1):
        table.add_row(
            str(idx),
            str(v.get("rule", v.get("packet_id", "—"))),
            str(v.get("severity", v.get("action", "—"))),
            str(v.get("description", v.get("governance_reason", "—"))),
            str(v.get("timestamp", "—")),
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Timeline Table
# ---------------------------------------------------------------------------

def render_timeline(agent_id: str, deltas: List[Dict[str, Any]]) -> None:
    """Render agent memory timeline as a vertical table."""
    console = get_console()

    table = Table(
        title=f"Timeline — Agent: {agent_id}",
        box=box.ROUNDED,
        border_style="bright_cyan",
        show_lines=True,
    )
    table.add_column("Tick", style="bright_cyan", justify="right", width=6)
    table.add_column("Intent", style="bright_magenta")
    table.add_column("Action", style="white")
    table.add_column("Outcome", min_width=8)
    table.add_column("Resources Δ", style="dim")
    table.add_column("Violation", width=4, justify="center")

    for d in deltas:
        outcome = d.get("outcome", "—")
        outcome_display = _colorize_status(outcome)
        violation = "🚨" if d.get("governance_violation", False) else ""
        res_delta = d.get("resources_delta", {})
        res_str = ", ".join(f"{k}:{v:+.1f}" for k, v in res_delta.items()) if res_delta else "—"

        table.add_row(
            str(d.get("tick", "—")),
            str(d.get("intent_type", "—")),
            str(d.get("action_type", "—")),
            outcome_display,
            res_str,
            violation,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Execution Log Table
# ---------------------------------------------------------------------------

def render_execution_log(logs: List[Dict[str, Any]], title: str = "Execution Log") -> None:
    """Render adapter execution log entries."""
    console = get_console()

    table = Table(
        title=title,
        box=box.ROUNDED,
        border_style="bright_cyan",
        show_lines=False,
    )
    table.add_column("Packet", style="bright_cyan", min_width=15)
    table.add_column("Action", style="white")
    table.add_column("Status")
    table.add_column("SHA-256", style="dim", max_width=16)
    table.add_column("Latency", justify="right")
    table.add_column("Time", style="dim")

    for entry in logs:
        status = entry.get("status", "unknown")
        status_display = _colorize_status(status)
        sha = entry.get("sha256_hash", "")[:16] + "..." if entry.get("sha256_hash") else "—"
        latency = entry.get("latency_ms")
        latency_str = f"{latency:.2f}ms" if latency is not None else "—"

        table.add_row(
            str(entry.get("packet_id", "—")),
            str(entry.get("action", "—")),
            status_display,
            sha,
            latency_str,
            str(entry.get("timestamp", "—")),
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Replay Result
# ---------------------------------------------------------------------------

def render_replay_result(
    original: Dict[str, Any],
    replayed: Optional[Dict[str, Any]] = None,
    match: Optional[bool] = None,
) -> None:
    """Render deterministic replay comparison."""
    console = get_console()

    # Original
    console.print(Panel(
        Syntax(
            __import__("json").dumps(original, indent=2, default=str),
            "json",
            theme="monokai",
        ),
        title="[bold white]Original Execution[/]",
        border_style="bright_cyan",
    ))

    if replayed is not None:
        console.print(Panel(
            Syntax(
                __import__("json").dumps(replayed, indent=2, default=str),
                "json",
                theme="monokai",
            ),
            title="[bold white]Replayed Execution[/]",
            border_style="bright_magenta",
        ))

    if match is not None:
        if match:
            console.print(Panel(
                "[bold bright_green]✅ Deterministic Match — Hashes are identical[/]",
                border_style="bright_green",
            ))
        else:
            console.print(Panel(
                "[bold bright_red]❌ Deterministic MISMATCH — Hashes diverge![/]",
                border_style="bright_red",
            ))


# ---------------------------------------------------------------------------
# Generic Helpers
# ---------------------------------------------------------------------------

def render_error(message: str) -> None:
    """Render an error panel."""
    get_console().print(Panel(
        f"[bold bright_red]❌ {message}[/]",
        border_style="bright_red",
        title="[bold white]Error[/]",
    ))


def render_success(message: str) -> None:
    """Render a success panel."""
    get_console().print(Panel(
        f"[bold bright_green]✅ {message}[/]",
        border_style="bright_green",
        title="[bold white]Success[/]",
    ))


def render_warning(message: str) -> None:
    """Render a warning panel."""
    get_console().print(Panel(
        f"[bold yellow]⚠️  {message}[/]",
        border_style="yellow",
        title="[bold white]Warning[/]",
    ))
