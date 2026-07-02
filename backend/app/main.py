from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import router
from .config import get_settings

settings = get_settings()

app = FastAPI(
    title="Global Equity Council API",
    version="1.0.0",
    description="Provenance-first, multi-agent global equity research. Not investment advice.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(router, prefix="/api")


static_dir = Path(settings.frontend_dist)
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
else:

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"name": settings.app_name, "docs": "/api/docs", "status": "ready"}
