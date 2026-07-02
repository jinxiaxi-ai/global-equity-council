import hashlib
from datetime import date, datetime
from typing import Any

from .fixtures import AS_OF
from .llm import DeterministicDemoLLM, LLMProvider
from .models import (
    AgentResult,
    AnalysisReport,
    DataMode,
    DebateTurn,
    Evidence,
    ValuationScenario,
    Vote,
)
from .providers import FixtureProvider

PERSONAS: list[dict[str, Any]] = [
    {
        "id": "buffett",
        "name": "Buffett-inspired",
        "method": "Moat, ROIC, owner earnings, capital allocation, and margin of safety.",
        "weights": (0.42, 0.18, 0.40),
    },
    {
        "id": "munger",
        "name": "Munger-inspired",
        "method": "Business quality, durability, management incentives, and predictability.",
        "weights": (0.48, 0.22, 0.30),
    },
    {
        "id": "damodaran",
        "name": "Damodaran-inspired",
        "method": "Narrative-to-numbers DCF, cost of capital, and assumption consistency.",
        "weights": (0.25, 0.50, 0.25),
    },
    {
        "id": "lynch",
        "name": "Peter Lynch-inspired",
        "method": "Lifecycle, understandable growth drivers, PEG, and operational momentum.",
        "weights": (0.25, 0.22, 0.53),
    },
    {
        "id": "wood",
        "name": "Cathie Wood-inspired",
        "method": "Innovation adoption curves, addressable market, and long-duration growth.",
        "weights": (0.15, 0.20, 0.65),
    },
    {
        "id": "burry",
        "name": "Burry-inspired",
        "method": "Contrarian accounting review, cycles, leverage, and consensus blind spots.",
        "weights": (0.20, 0.62, 0.18),
    },
]

FUNCTIONAL_AGENTS: list[tuple[str, str, str]] = [
    (
        "data_verification",
        "Data Verification Agent",
        "Checks provenance, periods, units, and gaps.",
    ),
    ("fundamental", "Fundamental Analysis Agent", "Normalizes operating and cash-flow trends."),
    ("valuation", "Valuation Agent", "Builds scenario valuation and sensitivity ranges."),
    (
        "industry",
        "Industry & Competitive Agent",
        "Assesses structure, moat, and competitive pressure.",
    ),
    ("macro_fx", "Macro & Currency Agent", "Separates operating drivers from currency exposure."),
    (
        "red_team",
        "Bear Case / Red-Team Agent",
        "Challenges consensus and searches for invalidation.",
    ),
    ("risk_manager", "Risk Manager", "Sizes uncertainty and monitors downside conditions."),
    (
        "chair",
        "Investment Committee Chair",
        "Aggregates evidence-weighted votes and disagreements.",
    ),
]


def _score(company: dict[str, Any], weights: tuple[float, float, float], price_ratio: float) -> int:
    quality = min(100.0, company["financials"][-1][4] * 2.4 + company["margin"] * 0.55)
    value = max(0.0, min(100.0, 60 + (1 - price_ratio) * 100))
    growth = max(0.0, min(100.0, company["growth"] * 3.3 + 35))
    return round(quality * weights[0] + value * weights[1] + growth * weights[2])


def _verdict(score: int) -> str:
    if score >= 72:
        return "Constructive"
    if score >= 55:
        return "Watch"
    return "Cautious"


def _scenario_list(company: dict[str, Any], currency: str) -> list[ValuationScenario]:
    values = company["scenario_values"]
    return [
        ValuationScenario(
            name="Bear",
            probability=0.25,
            growth_rate=max(0.5, company["growth"] * 0.45),
            operating_margin=max(3.0, company["margin"] * 0.78),
            discount_rate=11.5,
            terminal_growth=1.5,
            value_per_share=values[0],
            currency=currency,
            rationale="Slower demand, margin normalization, and a higher risk premium.",
        ),
        ValuationScenario(
            name="Base",
            probability=0.50,
            growth_rate=company["growth"] * 0.78,
            operating_margin=company["margin"] * 0.94,
            discount_rate=9.2,
            terminal_growth=2.5,
            value_per_share=values[1],
            currency=currency,
            rationale="Moderate execution near the normalized operating trend.",
        ),
        ValuationScenario(
            name="Bull",
            probability=0.25,
            growth_rate=company["growth"] * 1.18,
            operating_margin=company["margin"] * 1.06,
            discount_rate=8.0,
            terminal_growth=3.2,
            value_per_share=values[2],
            currency=currency,
            rationale="Strong execution, durable pricing, and favorable reinvestment returns.",
        ),
    ]


def _agent_result(
    definition: dict[str, Any],
    company: dict[str, Any],
    evidence: list[Evidence],
    score: int,
    price: float,
    base_value: float,
) -> AgentResult:
    verdict = _verdict(score)
    upside = (base_value / price - 1) * 100
    return AgentResult(
        agent_id=definition["id"],
        display_name=definition["name"],
        methodology=definition["method"],
        thesis=(
            f"{verdict}: normalized ROIC is {company['financials'][-1][4]:.1f}% and the "
            f"base case implies {upside:+.1f}% versus the dated fixture price."
        ),
        verdict=verdict,
        score=score,
        facts=[
            f"Latest fixture revenue is {company['financials'][-1][1]:,.0f} million {company['currency']}.",
            f"Latest normalized ROIC is {company['financials'][-1][4]:.1f}%.",
        ],
        inferences=[
            "Recent operating economics appear durable if normalized demand holds.",
            "The valuation range is more sensitive to discount rate than the point estimate suggests.",
        ],
        opinions=[
            "The current evidence supports monitoring a range, not treating a model output as precision."
        ],
        evidence=evidence,
        valuation=f"Bear/base/bull midpoint: {base_value:,.2f} {company['currency']}",
        assumptions=[
            "No unmodeled structural accounting restatement.",
            "Scenario discount rates remain appropriate for the local market and currency.",
        ],
        catalysts=[
            "Next annual or interim filing",
            "Evidence of margin or reinvestment-rate change",
        ],
        risks=[
            f"{company['debt_risk']} balance-sheet/capital-intensity risk",
            "Forecast, regulation, competition, and currency uncertainty",
        ],
        invalidation_conditions=[
            "ROIC falls below the cost of capital for two reporting periods.",
            "Free cash flow diverges materially from operating income without explanation.",
        ],
        confidence=round(min(0.93, 0.58 + len(company["financials"]) * 0.09), 2),
        disagreements=[
            "Growth-oriented members accept a wider valuation range than margin-of-safety members."
        ],
        missing_data=[
            "Real-time price and consensus estimates are intentionally unavailable in fixture mode."
        ],
    )


def _functional_result(
    agent_id: str,
    name: str,
    method: str,
    core_score: int,
    evidence: list[Evidence],
    company: dict[str, Any],
) -> AgentResult:
    adjustment = {
        "data_verification": 2,
        "fundamental": 4,
        "valuation": 0,
        "industry": 1,
        "macro_fx": -3,
        "red_team": -12,
        "risk_manager": -6,
        "chair": 0,
    }[agent_id]
    score = max(0, min(100, core_score + adjustment))
    return AgentResult(
        agent_id=agent_id,
        display_name=name,
        methodology=method,
        thesis=f"{_verdict(score)} after {method.lower()}",
        verdict=_verdict(score),
        score=score,
        facts=[f"Three normalized annual periods use {company['standard']}."],
        inferences=["Cross-market comparisons must retain the accounting-basis caveat."],
        opinions=[
            "Evidence quality is adequate for a demo research range, not a trade instruction."
        ],
        evidence=evidence,
        valuation=None,
        assumptions=["Fixture snapshots are interpreted only at their stated dates."],
        catalysts=["New primary-source filing"],
        risks=["Stale market snapshot", "Model specification risk"],
        invalidation_conditions=["Primary-source data conflicts with the normalized fixture."],
        confidence=0.78 if agent_id != "red_team" else 0.70,
        disagreements=["Point estimates should carry less weight than ranges."],
        missing_data=["No credentialed real-time market feed."],
    )


async def build_report(
    provider: FixtureProvider,
    asset_id: str,
    base_currency: str,
    llm: LLMProvider | None = None,
) -> AnalysisReport:
    asset = provider.asset(asset_id)
    company = provider.company(asset_id)
    price, financials, evidence = await _gather(provider, asset_id)
    scenarios = _scenario_list(company, asset.trading_currency)
    fx_rate = await provider.rate(asset.trading_currency, base_currency)
    converted = []
    if fx_rate:
        converted = [
            scenario.model_copy(
                update={
                    "value_per_share": round(scenario.value_per_share * fx_rate.rate, 2),
                    "currency": base_currency,
                }
            )
            for scenario in scenarios
        ]
    price_ratio = price.value / scenarios[1].value_per_share
    persona_results = [
        _agent_result(
            definition,
            company,
            evidence,
            _score(company, definition["weights"], price_ratio),
            price.value,
            scenarios[1].value_per_share,
        )
        for definition in PERSONAS
    ]
    persona_mean = round(sum(agent.score for agent in persona_results) / len(persona_results))
    functional_results = [
        _functional_result(agent_id, name, method, persona_mean, evidence, company)
        for agent_id, name, method in FUNCTIONAL_AGENTS
    ]
    agents = persona_results + functional_results
    votes = [
        Vote(
            agent_id=agent.agent_id,
            verdict=agent.verdict,
            score=agent.score,
            weight=1.2 if agent.agent_id in {"data_verification", "risk_manager", "chair"} else 1.0,
        )
        for agent in agents
    ]
    weighted_score = round(
        sum(vote.score * vote.weight for vote in votes) / sum(vote.weight for vote in votes)
    )
    active_llm = llm or DeterministicDemoLLM()
    chair_synthesis = await active_llm.complete(
        "committee-chair-synthesis",
        {
            "asset_id": asset_id,
            "score": weighted_score,
            "consensus": _verdict(weighted_score),
            "scenario_values": [scenario.value_per_share for scenario in scenarios],
            "disagreements": ["long-duration growth weight", "fixture-price staleness"],
            "instruction": (
                "Synthesize only supplied evidence in two sentences. State uncertainty; "
                "do not provide personalized advice."
            ),
        },
    )
    debate = _debate(persona_results, company, scenarios)
    report_hash = hashlib.sha256(f"{asset_id}|{base_currency}|{AS_OF}|v1".encode()).hexdigest()[:12]
    return AnalysisReport(
        report_id=f"gec-{report_hash}",
        analysis_date=date(2026, 1, 15),
        asset=asset,
        data_mode=DataMode.fixture,
        as_of=datetime.fromisoformat(AS_OF),
        source_summary=[
            company["source"]["name"],
            "ECB reference-rate normalized fixture" if fx_rate else "No FX conversion available",
        ],
        company_summary=company["summary"],
        industry_summary=company["industry"],
        accounting_note=company["accounting"],
        market_price=price,
        financials=financials,
        scenarios=scenarios,
        fx_rate=fx_rate,
        base_currency=base_currency,
        converted_scenarios=converted,
        sensitivity={
            "discount_rates": [8.0, 9.0, 10.0, 11.0],
            "terminal_growth_rates": [1.5, 2.0, 2.5, 3.0],
            "value_index": [118.0, 106.0, 95.0, 86.0],
        },
        agents=agents,
        debate=debate,
        votes=votes,
        consensus=_verdict(weighted_score),
        consensus_score=weighted_score,
        llm_provider=active_llm.__class__.__name__,
        chair_synthesis=chair_synthesis,
        major_disagreements=[
            "Innovation agents assign more weight to long-duration growth than value agents.",
            "Red-team and risk agents discount the fixture price because it is not real time.",
        ],
        catalysts=[
            "Next primary-source earnings release",
            "Capital allocation update",
            "Margin and free-cash-flow conversion trend",
        ],
        risks=[
            "Valuation compression if discount rates remain elevated",
            "Competition, regulation, execution, and local-currency exposure",
            "Fixture snapshots can differ materially from current market conditions",
        ],
        invalidation_conditions=[
            "Two consecutive periods of negative free cash flow without strategic explanation",
            "Structural loss of pricing power or market position",
            "Primary filing contradicts a material normalized input",
        ],
        missing_data=[
            "No real-time quote in credential-free demo mode",
            "No broker consensus or proprietary alternative data",
            "Scenario probabilities are methodology assumptions, not observed frequencies",
        ],
        evidence=evidence,
        disclaimer=(
            "For research and education only. Not investment advice, an offer, or a "
            "recommendation. Inspired-by agents do not represent or imply endorsement by any person."
        ),
    )


async def _gather(
    provider: FixtureProvider, asset_id: str
) -> tuple[Any, list[Any], list[Evidence]]:
    import asyncio

    price, financials, evidence = await asyncio.gather(
        provider.price(asset_id),
        provider.financials(asset_id),
        provider.evidence(asset_id),
    )
    return price, financials, evidence


def _debate(
    agents: list[AgentResult],
    company: dict[str, Any],
    scenarios: list[ValuationScenario],
) -> list[DebateTurn]:
    buffett, _munger, damodaran, _lynch, wood, burry = agents
    return [
        DebateTurn(
            sequence=1,
            agent_id=buffett.agent_id,
            agent_name=buffett.display_name,
            kind="opening",
            statement=(
                f"ROIC of {company['financials'][-1][4]:.1f}% is the anchor, but price must "
                "leave room for estimation error."
            ),
            evidence_ids=[0],
        ),
        DebateTurn(
            sequence=2,
            agent_id=wood.agent_id,
            agent_name=wood.display_name,
            kind="challenge",
            statement=(
                f"The base case may underweight adoption: normalized growth is "
                f"{company['growth']:.1f}% before optionality."
            ),
            challenges_agent_id=buffett.agent_id,
            evidence_ids=[0],
        ),
        DebateTurn(
            sequence=3,
            agent_id=burry.agent_id,
            agent_name=burry.display_name,
            kind="rebuttal",
            statement=(
                "A dated fixture price and adjusted metrics make false precision the immediate "
                "risk; downside should be framed by the bear case."
            ),
            challenges_agent_id=wood.agent_id,
            evidence_ids=[0],
        ),
        DebateTurn(
            sequence=4,
            agent_id=damodaran.agent_id,
            agent_name=damodaran.display_name,
            kind="synthesis",
            statement=(
                f"The defensible output is a {scenarios[0].value_per_share:,.0f}–"
                f"{scenarios[2].value_per_share:,.0f} range with explicit growth and discount rates."
            ),
            challenges_agent_id=burry.agent_id,
            evidence_ids=[0],
        ),
    ]
