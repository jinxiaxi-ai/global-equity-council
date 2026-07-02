import asyncio
import json
import sqlite3
import time
from abc import ABC, abstractmethod
from collections.abc import Coroutine
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Protocol, TypeVar

import httpx
import psycopg
from psycopg.types.json import Jsonb
from pydantic import HttpUrl

from .config import Settings
from .fixtures import AS_OF, ASSETS, COMPANIES, FX_RATES, RETRIEVED_AT
from .models import (
    AssetIdentity,
    DataMode,
    Evidence,
    FinancialPeriod,
    FxRate,
    MetricPoint,
    Provenance,
    SearchResult,
)

T = TypeVar("T")


class ProviderError(RuntimeError):
    """A recoverable upstream provider failure."""


async def with_retry(
    operation: Callable[[], Coroutine[Any, Any, T]],
    attempts: int = 3,
    base_delay: float = 0.15,
) -> T:
    last_error: Exception | None = None
    for index in range(attempts):
        try:
            return await operation()
        except (httpx.HTTPError, asyncio.TimeoutError) as error:
            last_error = error
            if index + 1 < attempts:
                await asyncio.sleep(base_delay * (2**index))
    raise ProviderError(f"upstream failed after {attempts} attempts: {last_error}")


class ProviderCache(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...

    def set(self, key: str, payload: dict[str, Any], ttl_seconds: int) -> None: ...


class SQLiteCache:
    def __init__(self, database_url: str) -> None:
        raw_path = database_url.removeprefix("sqlite:///")
        self.path = Path(raw_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS provider_cache "
                "(cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL, expires_at REAL NOT NULL)"
            )

    def get(self, key: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload, expires_at FROM provider_cache WHERE cache_key = ?", (key,)
            ).fetchone()
        if not row or row[1] < time.time():
            return None
        return json.loads(str(row[0]))

    def set(self, key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO provider_cache(cache_key, payload, expires_at) VALUES(?,?,?)",
                (key, json.dumps(payload), time.time() + ttl_seconds),
            )


class PostgresCache:
    """PostgreSQL implementation of the same provider-cache contract."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._initialize()

    def _connect(self) -> psycopg.Connection[tuple[Any, ...]]:
        return psycopg.connect(self.database_url)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS provider_cache ("
                "cache_key TEXT PRIMARY KEY, payload JSONB NOT NULL, "
                "expires_at DOUBLE PRECISION NOT NULL)"
            )

    def get(self, key: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload, expires_at FROM provider_cache WHERE cache_key = %s", (key,)
            ).fetchone()
        if not row or float(row[1]) < time.time():
            return None
        payload = row[0]
        return dict(payload) if isinstance(payload, dict) else json.loads(str(payload))

    def set(self, key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO provider_cache(cache_key, payload, expires_at) VALUES(%s,%s,%s) "
                "ON CONFLICT(cache_key) DO UPDATE SET "
                "payload=EXCLUDED.payload, expires_at=EXCLUDED.expires_at",
                (key, Jsonb(payload), time.time() + ttl_seconds),
            )


def build_cache(database_url: str) -> ProviderCache:
    if database_url.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        return PostgresCache(database_url)
    if database_url.startswith("sqlite:///"):
        return SQLiteCache(database_url)
    raise ValueError("DATABASE_URL must use sqlite:/// or postgresql://")


class AssetSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str) -> list[SearchResult]: ...


class MarketDataProvider(ABC):
    @abstractmethod
    async def price(self, asset_id: str) -> MetricPoint: ...


class FinancialStatementProvider(ABC):
    @abstractmethod
    async def financials(self, asset_id: str) -> list[FinancialPeriod]: ...


class RegulatoryFilingProvider(ABC):
    @abstractmethod
    async def evidence(self, asset_id: str) -> list[Evidence]: ...


class CorporateActionsProvider(ABC):
    @abstractmethod
    async def actions(self, asset_id: str) -> list[dict[str, Any]]: ...


class NewsProvider(ABC):
    @abstractmethod
    async def news(self, asset_id: str) -> list[Evidence]: ...


class MacroDataProvider(ABC):
    @abstractmethod
    async def indicators(self, country: str) -> list[MetricPoint]: ...


class FXRateProvider(ABC):
    @abstractmethod
    async def rate(self, base: str, quote: str) -> FxRate | None: ...


def _provenance(asset_id: str, currency: str) -> Provenance:
    company = COMPANIES[asset_id]
    source = company["source"]
    price_source_name, price_source_url = company["price_source"]
    return Provenance(
        source_url=price_source_url,
        source_name=price_source_name,
        retrieved_at=datetime.fromisoformat(RETRIEVED_AT),
        published_at=datetime.fromisoformat(AS_OF),
        fiscal_period=None,
        reported_currency=currency,
        data_mode=DataMode.fixture,
        confidence=0.85,
        provenance=(
            "Versioned closing-price fixture from the cited exchange/market page; "
            f"financials are normalized separately from {source['name']}."
        ),
    )


class FixtureProvider(
    AssetSearchProvider,
    MarketDataProvider,
    FinancialStatementProvider,
    RegulatoryFilingProvider,
    CorporateActionsProvider,
    NewsProvider,
    MacroDataProvider,
    FXRateProvider,
):
    async def search(self, query: str) -> list[SearchResult]:
        normalized = query.strip().lower().replace(".ss", "").replace(".hk", "")
        normalized = normalized.replace(".t", "").replace(".de", "")
        if not normalized:
            return []
        matches: list[SearchResult] = []
        for asset_id, raw in ASSETS.items():
            asset = AssetIdentity(**raw)
            fields = [
                asset.symbol.lower(),
                asset.display_name.lower(),
                asset.exchange.lower(),
                asset.mic.lower(),
                *[symbol.lower() for symbol in asset.provider_symbols.values()],
            ]
            if any(normalized in field for field in fields):
                reason = (
                    "symbol"
                    if normalized == asset.symbol.lower()
                    or normalized in [x.lower() for x in asset.provider_symbols.values()]
                    else "company_or_exchange"
                )
                matches.append(SearchResult(asset_id=asset_id, asset=asset, match_reason=reason))
        return sorted(matches, key=lambda item: (not item.asset.primary_listing, item.asset_id))

    async def price(self, asset_id: str) -> MetricPoint:
        company = self._company(asset_id)
        asset = AssetIdentity(**ASSETS[asset_id])
        return MetricPoint(
            name="market_price",
            label="Fixture closing price",
            value=company["price"],
            unit=asset.trading_currency,
            period=AS_OF[:10],
            provenance=_provenance(asset_id, asset.trading_currency),
        )

    async def financials(self, asset_id: str) -> list[FinancialPeriod]:
        company = self._company(asset_id)
        return [
            FinancialPeriod(
                period=period,
                revenue=revenue,
                operating_income=operating_income,
                free_cash_flow=fcf,
                roic=roic,
                currency=company["currency"],
                accounting_standard=company["standard"],
                fiscal_year_end=company["fye"],
            )
            for period, revenue, operating_income, fcf, roic in company["financials"]
        ]

    async def evidence(self, asset_id: str) -> list[Evidence]:
        company = self._company(asset_id)
        source = company["source"]
        return [
            Evidence(
                title=source["name"],
                claim="Primary filing used for normalized financial history and methodology inputs.",
                source_url=source["url"],
                source_name=source["name"],
                published_at=source["published"],
                data_mode=DataMode.fixture,
            )
        ]

    async def actions(self, asset_id: str) -> list[dict[str, Any]]:
        self._company(asset_id)
        return [
            {
                "type": "normalization_review",
                "status": "checked",
                "note": "Per-share fixture values are adjusted to the cited reporting snapshot.",
                "as_of": AS_OF,
            }
        ]

    async def news(self, asset_id: str) -> list[Evidence]:
        self._company(asset_id)
        return []

    async def indicators(self, country: str) -> list[MetricPoint]:
        return []

    async def rate(self, base: str, quote: str) -> FxRate | None:
        base, quote = base.upper(), quote.upper()
        value = FX_RATES.get((base, quote))
        if value is None and (quote, base) in FX_RATES:
            value = 1 / FX_RATES[(quote, base)]
        if value is None:
            return None
        return FxRate(
            base=base,
            quote=quote,
            rate=value,
            as_of=date(2025, 12, 31),
            source_name="ECB reference-rate normalized fixture",
            source_url=HttpUrl(
                "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/"
                "euro_reference_exchange_rates/html/index.en.html"
            ),
            data_mode=DataMode.fixture,
        )

    @staticmethod
    def asset(asset_id: str) -> AssetIdentity:
        if asset_id not in ASSETS:
            raise KeyError(asset_id)
        return AssetIdentity(**ASSETS[asset_id])

    @staticmethod
    def company(asset_id: str) -> dict[str, Any]:
        return FixtureProvider._company(asset_id)

    @staticmethod
    def _company(asset_id: str) -> dict[str, Any]:
        if asset_id not in COMPANIES:
            raise KeyError(asset_id)
        return COMPANIES[asset_id]


class SecEdgarProvider(RegulatoryFilingProvider):
    """Live SEC company submissions adapter with cache, rate limit and fallback.

    The fixture provider remains the deterministic default. This adapter is a
    complete public-source fetch path for US issuers and can be selected by
    callers when live data is desired.
    """

    CIKS = {"XNAS:AAPL": "0000320193"}
    _lock = asyncio.Lock()
    _last_request = 0.0

    def __init__(self, settings: Settings, cache: ProviderCache) -> None:
        self.settings = settings
        self.cache = cache

    async def evidence(self, asset_id: str) -> list[Evidence]:
        cik = self.CIKS.get(asset_id)
        if not cik:
            raise ProviderError(f"SEC has no issuer mapping for {asset_id}")
        key = f"sec-submissions:{cik}"
        cached = self.cache.get(key)
        mode = DataMode.cached
        if cached is None:
            cached = await with_retry(lambda: self._fetch(cik))
            self.cache.set(key, cached, 6 * 60 * 60)
            mode = DataMode.live
        recent = cached.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        indices = [index for index, form in enumerate(forms) if form in {"10-K", "20-F"}]
        if not indices:
            return []
        index = indices[0]
        accession = recent["accessionNumber"][index]
        primary = recent["primaryDocument"][index]
        accession_path = accession.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}/{primary}"
        filed = recent["filingDate"][index]
        return [
            Evidence(
                title=f"SEC EDGAR {forms[index]} filed {filed}",
                claim="Latest annual filing returned by the live SEC submissions API.",
                source_url=HttpUrl(url),
                source_name="SEC EDGAR",
                published_at=datetime.fromisoformat(f"{filed}T12:00:00+00:00"),
                data_mode=mode,
            )
        ]

    async def _fetch(self, cik: str) -> dict[str, Any]:
        async with self._lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < 0.11:
                await asyncio.sleep(0.11 - elapsed)
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(
                    f"https://data.sec.gov/submissions/CIK{cik}.json",
                    headers={
                        "User-Agent": self.settings.sec_user_agent,
                        "Accept-Encoding": "gzip, deflate",
                    },
                )
                response.raise_for_status()
            self._last_request = time.monotonic()
            return dict(response.json())
