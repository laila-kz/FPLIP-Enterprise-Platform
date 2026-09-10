"""
FPLIP API — FastAPI application entry point.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.routers import health, oee, scrap, ml, ai, context
from api.dependencies.auth import verify_api_key

app = FastAPI(
    title="FPLIP API",
    version="1.0.0",
    description="Factory Performance & Loss Intelligence Platform API",
)

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public router
app.include_router(health.router)

# Protected routers (require X-Internal-Key)
auth_dependencies = [Depends(verify_api_key)]
app.include_router(context.router, dependencies=auth_dependencies)
app.include_router(oee.router, dependencies=auth_dependencies)
app.include_router(scrap.router, dependencies=auth_dependencies)
app.include_router(ml.router, dependencies=auth_dependencies)
app.include_router(ai.router, dependencies=auth_dependencies)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "FPLIP API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }