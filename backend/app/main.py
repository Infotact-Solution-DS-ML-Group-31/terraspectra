"""
TerraSpectra FastAPI Application Entrypoint.
Provides RESTful APIs for exploratory hyperspectral analytics.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import (
    API_VERSION,
    APP_NAME,
    FIGURES_DIR
)
from backend.app.api import (
    health,
    datasets,
    spectral,
    roi,
    reports,
    pca
)

app = FastAPI(
    title=APP_NAME,
    version=API_VERSION,
    description=(
        "Exploratory Hyperspectral Analytics Platform for agricultural disease research. "
        "Provides REST endpoints for cube inspection, spectral profiling, ROI contrast, "
        "and data quality verification."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

# CORS middleware for explicit local development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static figures directory for figure retrieval
if FIGURES_DIR.exists():
    app.mount("/static/figures", StaticFiles(directory=str(FIGURES_DIR)), name="figures")

# Register API routers with /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(spectral.router, prefix="/api")
app.include_router(roi.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(pca.router, prefix="/api")


@app.get("/")
def root():
    """Root endpoint returning platform information."""
    return {
        "message": "Welcome to TerraSpectra Hyperspectral Analytics API",
        "version": API_VERSION,
        "docs_url": "/docs",
        "health_url": "/api/health",
        "datasets_url": "/api/datasets"
    }
