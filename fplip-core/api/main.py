"""
FPLIP API — FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import health, oee, scrap, ml, ai, context

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

# Register routers
app.include_router(health.router)
app.include_router(context.router)
app.include_router(oee.router)
app.include_router(scrap.router)
app.include_router(ml.router)
app.include_router(ai.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "FPLIP API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }