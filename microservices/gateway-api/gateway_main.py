"""
gateway_main.py
Main Gateway API application combining all RCT services

Services integrated:
1. SignedAI (Verification)
2. ArtentAI (Creation) - Future
3. Genome API (Creator Profile)
4. Kernel (Routing) - Future

Port: 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, '06_products_rctlabs_artentai_signedai'))
sys.path.insert(0, os.path.join(project_root, '10_kernel_runtime'))
sys.path.insert(0, current_dir)  # Add 01_gateway to path

# Import routers
try:
    import genome_api
    genome_router = genome_api.router
    genome_available = True
except ImportError as e:
    print(f"Warning: Genome API not available: {e}")
    genome_available = False

try:
    from signedai.api import app as signedai_app
    signedai_available = True
except ImportError as e:
    print(f"Warning: SignedAI not available: {e}")
    signedai_available = False

# Create main app
app = FastAPI(
    title="RCT Gateway API",
    description="Unified Gateway for RCT Ecosystem (SignedAI + Genome + Kernel)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (for Frontend widget)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "service": "RCT Gateway API",
        "version": "1.0.0",
        "status": "operational",
        "services": {
            "genome": "available" if genome_available else "unavailable",
            "signedai": "available" if signedai_available else "unavailable"
        },
        "endpoints": {
            "genome": "/api/genome/*",
            "signedai": "/signedai/*",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "gateway": "healthy",
        "services": {}
    }
    
    # Check Genome API
    if genome_available:
        try:
            from genome_api import get_manager
            manager = get_manager()
            health_status["services"]["genome"] = {
                "status": "healthy",
                "genome_version": "4.0"
            }
        except Exception as e:
            health_status["services"]["genome"] = {
                "status": "degraded",
                "error": str(e)
            }
    else:
        health_status["services"]["genome"] = {"status": "unavailable"}
    
    # Check SignedAI
    if signedai_available:
        health_status["services"]["signedai"] = {"status": "healthy"}
    else:
        health_status["services"]["signedai"] = {"status": "unavailable"}
    
    return health_status

# Mount routers
if genome_available:
    app.include_router(genome_router)
    print("✅ Genome API mounted at /api/genome")

if signedai_available:
    # Mount SignedAI routes (if available)
    try:
        from signedai.api import router as signedai_router
        app.include_router(signedai_router, prefix="/signedai", tags=["signedai"])
        print("✅ SignedAI mounted at /signedai")
    except Exception as e:
        print(f"⚠️ Could not mount SignedAI router: {e}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Endpoint {request.url.path} not found",
            "available_endpoints": ["/", "/health", "/api/genome/*", "/docs"]
        }
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc)
        }
    )

# Run server
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 Starting RCT Gateway API")
    print("="*60)
    print(f"📍 Gateway URL: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🧬 Genome API: http://localhost:8000/api/genome/health")
    print("="*60 + "\n")
    
    uvicorn.run(
        "gateway_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
