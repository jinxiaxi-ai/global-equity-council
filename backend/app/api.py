import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from .committee import build_report
from .config import Settings, get_settings
from .llm import build_llm
from .models import (
    AnalysisReport,
    AnalysisRequest,
    AssetIdentity,
    HealthResponse,
    SearchResult,
)
from .providers import FixtureProvider

router = APIRouter()
provider = FixtureProvider()
_requests: dict[str, deque[float]] = defaultdict(deque)
settings_dependency = Depends(get_settings)


def rate_limit(request: Request) -> None:
    """Small process-local abuse guard for public demo deployments."""
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _requests[client]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= 60:
        raise HTTPException(status_code=429, detail="Rate limit exceeded; retry in one minute.")
    bucket.append(now)


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = settings_dependency) -> HealthResponse:
    llm = build_llm(settings)
    return HealthResponse(
        status="ok",
        data_provider=settings.data_provider,
        llm_provider=llm.__class__.__name__,
        database="sqlite" if settings.database_url.startswith("sqlite") else "postgresql",
    )


@router.get("/assets/search", response_model=list[SearchResult])
async def search_assets(
    request: Request,
    q: str = Query(min_length=1, max_length=80),
) -> list[SearchResult]:
    rate_limit(request)
    return await provider.search(q)


@router.get("/assets/{mic}/{symbol}", response_model=AssetIdentity)
async def get_asset(mic: str, symbol: str) -> AssetIdentity:
    try:
        return provider.asset(f"{mic.upper()}:{symbol.upper()}")
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Asset not found") from error


@router.post("/analysis", response_model=AnalysisReport)
async def analyze(request: Request, payload: AnalysisRequest) -> AnalysisReport:
    rate_limit(request)
    try:
        settings = get_settings()
        return await build_report(
            provider,
            payload.asset_id.upper(),
            payload.base_currency.upper(),
            build_llm(settings),
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Asset is unsupported in demo mode. Search for a fixture-backed listing.",
        ) from error
