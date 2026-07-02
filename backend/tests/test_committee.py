import pytest

from app.committee import FUNCTIONAL_AGENTS, PERSONAS, build_report
from app.llm import LLMProvider
from app.providers import FixtureProvider


class RecordingLLM(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, system: str, payload: dict[str, object]) -> str:
        self.calls += 1
        assert system == "committee-chair-synthesis"
        assert payload["asset_id"] == "XNAS:AAPL"
        return "Recorded chair synthesis."


@pytest.mark.asyncio
async def test_report_is_deterministic() -> None:
    provider = FixtureProvider()
    first = await build_report(provider, "XNAS:AAPL", "USD")
    second = await build_report(provider, "XNAS:AAPL", "USD")
    assert first.model_dump_json() == second.model_dump_json()
    assert first.report_id == second.report_id


@pytest.mark.asyncio
async def test_all_agents_return_strict_claim_categories() -> None:
    report = await build_report(FixtureProvider(), "XHKG:0700", "USD")
    assert len(report.agents) == len(PERSONAS) + len(FUNCTIONAL_AGENTS) == 14
    for agent in report.agents:
        assert agent.methodology
        assert agent.facts
        assert agent.inferences
        assert agent.opinions
        assert agent.evidence
        assert 0 <= agent.score <= 100
        assert 0 <= agent.confidence <= 1
        assert agent.invalidation_conditions
        assert agent.missing_data


@pytest.mark.asyncio
async def test_scenario_and_fx_normalization() -> None:
    report = await build_report(FixtureProvider(), "XTKS:7203", "USD")
    assert [item.name for item in report.scenarios] == ["Bear", "Base", "Bull"]
    assert sum(item.probability for item in report.scenarios) == 1
    assert report.fx_rate
    assert report.fx_rate.as_of.isoformat() == "2025-12-31"
    assert all(item.currency == "USD" for item in report.converted_scenarios)
    assert report.asset.reporting_currency == "JPY"
    assert report.market_price.provenance.reported_currency == "JPY"


@pytest.mark.asyncio
async def test_report_declares_uncertainty_and_disclaimer() -> None:
    report = await build_report(FixtureProvider(), "XSHG:600519", "CNY")
    assert report.data_mode.value == "fixture"
    assert report.missing_data
    assert report.major_disagreements
    assert "Not investment advice" in report.disclaimer
    assert "do not represent" in report.disclaimer


@pytest.mark.asyncio
async def test_zh_locale_localizes_analysis_content() -> None:
    report = await build_report(FixtureProvider(), "XNAS:AAOI", "USD", locale="zh-CN")
    assert report.company_summary.startswith("Applied Optoelectronics")
    assert report.scenarios[0].name == "熊市"
    assert report.agents[0].facts[0].startswith("最新 fixture 收入")
    assert report.debate[0].statement.endswith("留出空间。")
    assert "不构成投资建议" in report.disclaimer


@pytest.mark.asyncio
async def test_configured_llm_is_used_for_chair_synthesis() -> None:
    llm = RecordingLLM()
    report = await build_report(FixtureProvider(), "XNAS:AAPL", "USD", llm)
    assert llm.calls == 1
    assert report.llm_provider == "RecordingLLM"
    assert report.chair_synthesis == "Recorded chair synthesis."
