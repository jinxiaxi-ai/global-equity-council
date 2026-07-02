import pytest

from app.fixtures import ASSETS
from app.models import DataMode
from app.providers import FixtureProvider, SQLiteCache, build_cache

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
