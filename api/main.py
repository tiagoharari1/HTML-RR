"""
FastAPI app principal — monta todas las rutas con prefijo /api.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import build, config, data, export, upload

app = FastAPI(
    title="RR AI API",
    description="Backend de proyección Run Rate HTML/B2B",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(config.router, prefix="/api", tags=["Config"])
app.include_router(build.router,  prefix="/api", tags=["Build"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(data.router,   prefix="/api", tags=["Data"])
