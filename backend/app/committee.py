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


def _is_zh(locale: str) -> bool:
    return locale.lower().startswith("zh")


def _company_text(company: dict[str, Any], key: str, locale: str) -> str:
    if _is_zh(locale):
        return str(company.get(f"{key}_zh", company[key]))
    return str(company[key])


def _debt_risk(company: dict[str, Any], locale: str) -> str:
    if _is_zh(locale):
        return str(
            company.get(
                "debt_risk_zh",
                {"Low": "较低", "Medium": "中等", "High": "较高"}.get(
                    company["debt_risk"], company["debt_risk"]
                ),
            )
        )
    return str(company["debt_risk"])


def _agent_name(definition: dict[str, Any], locale: str) -> str:
    if not _is_zh(locale):
        return str(definition["name"])
    names = {
        "buffett": "巴菲特风格",
        "munger": "芒格风格",
        "damodaran": "达莫达兰风格",
        "lynch": "彼得·林奇风格",
        "wood": "凯茜·伍德风格",
        "burry": "迈克尔·伯里风格",
    }
    return names.get(str(definition["id"]), str(definition["name"]))


def _agent_method(definition: dict[str, Any], locale: str) -> str:
    if not _is_zh(locale):
        return str(definition["method"])
    methods = {
        "buffett": "护城河、ROIC、所有者收益、资本配置和安全边际。",
        "munger": "商业质量、耐久性、管理层激励和可预测性。",
        "damodaran": "叙事到数字的 DCF、资本成本和假设一致性。",
        "lynch": "生命周期、可理解的增长驱动、PEG 和经营动量。",
        "wood": "创新采用曲线、可服务市场空间和长期增长。",
        "burry": "逆向会计审查、周期、杠杆和共识盲点。",
    }
    return methods.get(str(definition["id"]), str(definition["method"]))


def _functional_name(agent_id: str, name: str, locale: str) -> str:
    if not _is_zh(locale):
        return name
    names = {
        "data_verification": "数据核验 Agent",
        "fundamental": "基本面分析 Agent",
        "valuation": "估值 Agent",
        "industry": "行业与竞争 Agent",
        "macro_fx": "宏观与汇率 Agent",
        "red_team": "空方 / 红队 Agent",
        "risk_manager": "风险管理 Agent",
        "chair": "投资委员会主席",
    }
    return names[agent_id]


def _functional_method(agent_id: str, method: str, locale: str) -> str:
    if not _is_zh(locale):
        return method
    methods = {
        "data_verification": "核验来源、期间、单位和数据缺口。",
        "fundamental": "标准化经营趋势和现金流趋势。",
        "valuation": "构建情景估值和敏感性区间。",
        "industry": "评估行业结构、护城河和竞争压力。",
        "macro_fx": "区分经营驱动与汇率敞口。",
        "red_team": "挑战共识并寻找失效条件。",
        "risk_manager": "衡量不确定性并监控下行条件。",
        "chair": "汇总证据加权投票和主要分歧。",
    }
    return methods[agent_id]


def _score(company: dict[str, Any], weights: tuple[float, float, float], price_ratio: float) -> int:
    quality = min(100.0, company["financials"][-1][4] * 2.4 + company["margin"] * 0.55)
    value = max(0.0, min(100.0, 60 + (1 - price_ratio) * 100))
    growth = max(0.0, min(100.0, company["growth"] * 3.3 + 35))
    return round(quality * weights[0] + value * weights[1] + growth * weights[2])


def _verdict(score: int, locale: str = "en-US") -> str:
    if score >= 72:
        return "建设性" if _is_zh(locale) else "Constructive"
    if score >= 55:
        return "观察" if _is_zh(locale) else "Watch"
    return "谨慎" if _is_zh(locale) else "Cautious"


def _scenario_list(
    company: dict[str, Any], currency: str, locale: str = "en-US"
) -> list[ValuationScenario]:
    values = company["scenario_values"]
    if _is_zh(locale):
        return [
            ValuationScenario(
                name="熊市",
                probability=0.25,
                growth_rate=max(0.5, company["growth"] * 0.45),
                operating_margin=max(3.0, company["margin"] * 0.78),
                discount_rate=11.5,
                terminal_growth=1.5,
                value_per_share=values[0],
                currency=currency,
                rationale="需求放缓、利润率正常化，并叠加更高风险溢价。",
            ),
            ValuationScenario(
                name="基准",
                probability=0.50,
                growth_rate=company["growth"] * 0.78,
                operating_margin=company["margin"] * 0.94,
                discount_rate=9.2,
                terminal_growth=2.5,
                value_per_share=values[1],
                currency=currency,
                rationale="执行表现接近标准化经营趋势，增长和利润率保持中性假设。",
            ),
            ValuationScenario(
                name="牛市",
                probability=0.25,
                growth_rate=company["growth"] * 1.18,
                operating_margin=company["margin"] * 1.06,
                discount_rate=8.0,
                terminal_growth=3.2,
                value_per_share=values[2],
                currency=currency,
                rationale="执行强劲、定价能力延续，且再投资回报更有利。",
            ),
        ]
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
    locale: str = "en-US",
) -> AgentResult:
    verdict = _verdict(score, locale)
    upside = (base_value / price - 1) * 100
    if _is_zh(locale):
        return AgentResult(
            agent_id=definition["id"],
            display_name=_agent_name(definition, locale),
            methodology=_agent_method(definition, locale),
            thesis=(
                f"{verdict}：标准化 ROIC 为 {company['financials'][-1][4]:.1f}%，"
                f"基准情景相对已注明日期的 fixture 价格隐含 {upside:+.1f}% 空间。"
            ),
            verdict=verdict,
            score=score,
            facts=[
                f"最新 fixture 收入为 {company['financials'][-1][1]:,.0f} 百万 {company['currency']}。",
                f"最新标准化 ROIC 为 {company['financials'][-1][4]:.1f}%。",
            ],
            inferences=[
                "如果标准化需求成立，近期经营经济性具备一定延续性。",
                "估值区间对折现率的敏感度高于单一点位估值显示的程度。",
            ],
            opinions=["当前证据更适合监控一个估值范围，而不是把模型输出当作精确价格。"],
            evidence=evidence,
            valuation=f"熊市/基准/牛市中点：{base_value:,.2f} {company['currency']}",
            assumptions=[
                "不存在未建模的结构性会计重述。",
                "情景折现率仍适合该本地市场和币种。",
            ],
            catalysts=[
                "下一次年度或中期披露",
                "利润率或再投资回报率变化的证据",
            ],
            risks=[
                f"{_debt_risk(company, locale)}的资产负债表/资本密集度风险",
                "预测、监管、竞争和汇率不确定性",
            ],
            invalidation_conditions=[
                "ROIC 连续两个报告期低于资本成本。",
                "自由现金流与营业利润出现重大背离且缺乏解释。",
            ],
            confidence=round(min(0.93, 0.58 + len(company["financials"]) * 0.09), 2),
            disagreements=["成长导向成员比安全边际成员接受更宽的估值区间。"],
            missing_data=["fixture 模式刻意不包含实时价格和卖方一致预期。"],
        )
    return AgentResult(
        agent_id=definition["id"],
        display_name=_agent_name(definition, locale),
        methodology=_agent_method(definition, locale),
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
    locale: str = "en-US",
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
    localized_name = _functional_name(agent_id, name, locale)
    localized_method = _functional_method(agent_id, method, locale)
    if _is_zh(locale):
        return AgentResult(
            agent_id=agent_id,
            display_name=localized_name,
            methodology=localized_method,
            thesis=f"{localized_method}后结论为{_verdict(score, locale)}。",
            verdict=_verdict(score, locale),
            score=score,
            facts=[f"三期标准化年度数据采用 {company['standard']}。"],
            inferences=["跨市场比较必须保留会计准则差异这一前提。"],
            opinions=["证据质量足以支持 demo 研究区间，但不能作为交易指令。"],
            evidence=evidence,
            valuation=None,
            assumptions=["fixture 快照只应按其声明日期解释。"],
            catalysts=["新的主要来源披露"],
            risks=["市场快照陈旧", "模型设定风险"],
            invalidation_conditions=["主要来源数据与标准化 fixture 出现冲突。"],
            confidence=0.78 if agent_id != "red_team" else 0.70,
            disagreements=["估值点位应低于估值区间本身的权重。"],
            missing_data=["没有接入需凭证的实时行情源。"],
        )
    return AgentResult(
        agent_id=agent_id,
        display_name=localized_name,
        methodology=localized_method,
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
    locale: str = "en-US",
) -> AnalysisReport:
    asset = provider.asset(asset_id)
    company = provider.company(asset_id)
    price, financials, evidence = await _gather(provider, asset_id)
    price = _localized_price(price, locale)
    evidence = _localized_evidence(evidence, locale)
    scenarios = _scenario_list(company, asset.trading_currency, locale)
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
            locale,
        )
        for definition in PERSONAS
    ]
    persona_mean = round(sum(agent.score for agent in persona_results) / len(persona_results))
    functional_results = [
        _functional_result(agent_id, name, method, persona_mean, evidence, company, locale)
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
            "consensus": _verdict(weighted_score, locale),
            "scenario_values": [scenario.value_per_share for scenario in scenarios],
            "disagreements": (
                ["长期增长权重", "fixture 价格时效性"]
                if _is_zh(locale)
                else ["long-duration growth weight", "fixture-price staleness"]
            ),
            "locale": locale,
            "instruction": (
                "只综合已提供证据，用两句话说明不确定性；不要提供个性化投资建议。"
                if _is_zh(locale)
                else (
                    "Synthesize only supplied evidence in two sentences. State uncertainty; "
                    "do not provide personalized advice."
                )
            ),
        },
    )
    debate = _debate(persona_results, company, scenarios, locale)
    report_hash = hashlib.sha256(
        f"{asset_id}|{base_currency}|{locale}|{AS_OF}|v2".encode()
    ).hexdigest()[:12]
    return AnalysisReport(
        report_id=f"gec-{report_hash}",
        analysis_date=date(2026, 1, 15),
        asset=asset,
        data_mode=DataMode.fixture,
        as_of=datetime.fromisoformat(AS_OF),
        source_summary=[
            company["source"]["name"],
            (
                "ECB 参考汇率标准化 fixture"
                if fx_rate and _is_zh(locale)
                else "ECB reference-rate normalized fixture"
                if fx_rate
                else "没有可用外汇换算"
                if _is_zh(locale)
                else "No FX conversion available"
            ),
        ],
        company_summary=_company_text(company, "summary", locale),
        industry_summary=_company_text(company, "industry", locale),
        accounting_note=_company_text(company, "accounting", locale),
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
        consensus=_verdict(weighted_score, locale),
        consensus_score=weighted_score,
        llm_provider=active_llm.__class__.__name__,
        chair_synthesis=chair_synthesis,
        major_disagreements=_major_disagreements(locale),
        catalysts=_catalysts(locale),
        risks=_risks(locale),
        invalidation_conditions=_invalidation_conditions(locale),
        missing_data=_missing_data(locale),
        evidence=evidence,
        disclaimer=_disclaimer(locale),
    )


def _localized_price(price: Any, locale: str) -> Any:
    if not _is_zh(locale):
        return price
    return price.model_copy(
        update={
            "label": "Fixture 收盘价",
            "provenance": price.provenance.model_copy(
                update={
                    "provenance": (
                        "来自所引用交易所/市场页面的版本化收盘价 fixture；"
                        "财务数据另按主要来源披露进行标准化。"
                    )
                }
            ),
        }
    )


def _localized_evidence(evidence: list[Evidence], locale: str) -> list[Evidence]:
    if not _is_zh(locale):
        return evidence
    return [
        item.model_copy(update={"claim": "该主要披露用于标准化财务历史和方法论输入。"})
        for item in evidence
    ]


def _major_disagreements(locale: str) -> list[str]:
    if _is_zh(locale):
        return [
            "创新导向 agent 比价值导向 agent 更重视长期增长。",
            "红队和风险 agent 因 fixture 价格不是实时数据而下调其权重。",
        ]
    return [
        "Innovation agents assign more weight to long-duration growth than value agents.",
        "Red-team and risk agents discount the fixture price because it is not real time.",
    ]


def _catalysts(locale: str) -> list[str]:
    if _is_zh(locale):
        return [
            "下一次主要来源业绩披露",
            "资本配置更新",
            "利润率和自由现金流转化趋势",
        ]
    return [
        "Next primary-source earnings release",
        "Capital allocation update",
        "Margin and free-cash-flow conversion trend",
    ]


def _risks(locale: str) -> list[str]:
    if _is_zh(locale):
        return [
            "若折现率维持高位，估值倍数可能压缩",
            "竞争、监管、执行和本币敞口风险",
            "fixture 快照可能与当前市场状况存在重大差异",
        ]
    return [
        "Valuation compression if discount rates remain elevated",
        "Competition, regulation, execution, and local-currency exposure",
        "Fixture snapshots can differ materially from current market conditions",
    ]


def _invalidation_conditions(locale: str) -> list[str]:
    if _is_zh(locale):
        return [
            "自由现金流连续两个期间为负且缺乏战略性解释",
            "定价能力或市场地位发生结构性丧失",
            "主要披露与重要标准化输入相矛盾",
        ]
    return [
        "Two consecutive periods of negative free cash flow without strategic explanation",
        "Structural loss of pricing power or market position",
        "Primary filing contradicts a material normalized input",
    ]


def _missing_data(locale: str) -> list[str]:
    if _is_zh(locale):
        return [
            "无凭证 demo 模式不含实时行情",
            "没有卖方一致预期或专有另类数据",
            "情景概率是方法论假设，不是观察到的频率",
        ]
    return [
        "No real-time quote in credential-free demo mode",
        "No broker consensus or proprietary alternative data",
        "Scenario probabilities are methodology assumptions, not observed frequencies",
    ]


def _disclaimer(locale: str) -> str:
    if _is_zh(locale):
        return (
            "仅供研究和教育用途。不构成投资建议、要约或推荐。"
            "“风格化”agent 不代表任何真实人物，也不暗示其认可。"
        )
    return (
        "For research and education only. Not investment advice, an offer, or a "
        "recommendation. Inspired-by agents do not represent or imply endorsement by any person."
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
    locale: str = "en-US",
) -> list[DebateTurn]:
    buffett, _munger, damodaran, _lynch, wood, burry = agents
    if _is_zh(locale):
        return [
            DebateTurn(
                sequence=1,
                agent_id=buffett.agent_id,
                agent_name=buffett.display_name,
                kind="opening",
                statement=(
                    f"{company['financials'][-1][4]:.1f}% 的 ROIC 是分析锚点，"
                    "但价格必须给估计误差留出空间。"
                ),
                evidence_ids=[0],
            ),
            DebateTurn(
                sequence=2,
                agent_id=wood.agent_id,
                agent_name=wood.display_name,
                kind="challenge",
                statement=(
                    f"基准情景可能低估采用曲线：标准化增长率为 "
                    f"{company['growth']:.1f}%，尚未充分计入可选性。"
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
                    "已注明日期的 fixture 价格和调整后指标会带来虚假精确感；"
                    "下行风险应以熊市情景来框定。"
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
                    f"更稳健的输出是 {scenarios[0].value_per_share:,.0f}–"
                    f"{scenarios[2].value_per_share:,.0f} 的区间，并明确增长率与折现率。"
                ),
                challenges_agent_id=burry.agent_id,
                evidence_ids=[0],
            ),
        ]
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
