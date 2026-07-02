import pytest

from app.config import Settings
from app.fixtures import ASSETS
from app.models import DataMode
from app.providers import (
    BYOKMarketDataProvider,
    FixtureProvider,
    SQLiteCache,
    build_cache,
    build_data_provider,
)

REQUIRED_ASSETS = [
    "XNAS:AAPL",
    "XSHG:600519",
    "XHKG:0700",
    "XTKS:7203",
    "XETR:SAP",
    "XNAS:MU",
    "XNAS:AAOI",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("asset_id", REQUIRED_ASSETS)
async def test_five_market_provider_contract(asset_id: str) -> None:
    provider = FixtureProvider()
    asset = provider.asset(asset_id)
    price = await provider.price(asset_id)
    financials = await provider.financials(asset_id)
    evidence = await provider.evidence(asset_id)

    assert asset.asset_id == asset_id
    assert asset.mic and asset.exchange and asset.timezone
    assert asset.trading_currency in {"USD", "CNY", "HKD", "JPY", "EUR"}
    assert len(financials) == 3
    assert all(
        row.currency and row.accounting_standard and row.fiscal_year_end for row in financials
    )
    assert price.provenance.data_mode is DataMode.fixture
    assert price.provenance.source_url
    assert evidence[0].source_url


@pytest.mark.asyncio
async def test_ambiguous_ticker_returns_listing_choices() -> None:
    results = await FixtureProvider().search("SAP")
    assert [item.asset_id for item in results] == ["XETR:SAP", "XNYS:SAP"]
    assert results[0].asset.primary_listing is True
    assert results[1].asset.primary_listing is False


@pytest.mark.asyncio
async def test_provider_symbols_and_company_name_search() -> None:
    provider = FixtureProvider()
    assert (await provider.search("600519.SS"))[0].asset_id == "XSHG:600519"
    assert (await provider.search("Tencent"))[0].asset_id == "XHKG:0700"
    assert (await provider.search("Tokyo Stock"))[0].asset_id == "XTKS:7203"
    assert (await provider.search("micron"))[0].asset_id == "XNAS:MU"
    assert (await provider.search("Applied Opto"))[0].asset_id == "XNAS:AAOI"


def test_ticker_is_not_identity() -> None:
    assert ASSETS["XETR:SAP"]["symbol"] == ASSETS["XNYS:SAP"]["symbol"]
    assert ASSETS["XETR:SAP"]["mic"] != ASSETS["XNYS:SAP"]["mic"]


def test_sqlite_cache_contract_and_database_selection(tmp_path) -> None:
    cache = build_cache(f"sqlite:///{tmp_path / 'provider.db'}")
    assert isinstance(cache, SQLiteCache)
    cache.set("quote:AAPL", {"price": 100}, ttl_seconds=30)
    assert cache.get("quote:AAPL") == {"price": 100}


def test_rejects_unknown_database_scheme() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        build_cache("mysql://localhost/example")


@pytest.mark.asyncio
async def test_byok_provider_overlays_live_quote_and_cache(monkeypatch, tmp_path) -> None:
    settings = Settings(
        data_provider="twelvedata",
        market_data_api_key="user-key",
        database_url=f"sqlite:///{tmp_path / 'provider.db'}",
    )
    provider = BYOKMarketDataProvider(settings, build_cache(settings.database_url))

    async def fake_fetch(provider_name: str, asset_id: str, key: str) -> dict[str, object]:
        assert provider_name == "twelvedata"
        assert asset_id == "XNAS:AAOI"
        assert key == "user-key"
        return {
            "provider": "twelvedata",
            "source_name": "Twelve Data quote API",
            "source_url": "https://twelvedata.com/docs#quote",
            "symbol": "AAOI",
            "price": 42.25,
            "currency": "USD",
            "period": "2026-07-02",
            "retrieved_at": "2026-07-02T14:00:00+00:00",
            "confidence": 0.92,
            "provenance": "User-supplied Twelve Data API key fetched the latest available quote.",
        }

    monkeypatch.setattr(provider, "_fetch_quote", fake_fetch)
    live = await provider.price("XNAS:AAOI")
    assert live.value == 42.25
    assert live.provenance.data_mode is DataMode.live
    assert live.period == "2026-07-02"

    async def unexpected_fetch(provider_name: str, asset_id: str, key: str) -> dict[str, object]:
        raise AssertionError("cached quote should not refetch")

    monkeypatch.setattr(provider, "_fetch_quote", unexpected_fetch)
    cached = await provider.price("XNAS:AAOI")
    assert cached.value == 42.25
    assert cached.provenance.data_mode is DataMode.cached


@pytest.mark.asyncio
async def test_byok_provider_without_key_keeps_fixture_mode(tmp_path) -> None:
    settings = Settings(
        data_provider="finnhub",
        market_data_api_key=None,
        database_url=f"sqlite:///{tmp_path / 'provider.db'}",
    )
    provider = build_data_provider(settings)
    price = await provider.price("XNAS:MU")
    assert price.provenance.data_mode is DataMode.fixture
