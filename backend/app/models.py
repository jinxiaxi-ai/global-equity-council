from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class DataMode(str, Enum):
    live = "live"
    cached = "cached"
    fixture = "fixture"


class AssetIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    display_name: str
    exchange: str
    mic: str = Field(min_length=4, max_length=4)
    country: str
    security_type: str
    trading_currency: str = Field(min_length=3, max_length=3)
    reporting_currency: str = Field(min_length=3, max_length=3)
    timezone: str
    locale: str
    isin: str | None = None
    provider_symbols: dict[str, str]
    primary_listing: bool

    @property
    def asset_id(self) -> str:
        return f"{self.mic}:{self.symbol}"


class Provenance(BaseModel):
    source_url: HttpUrl
    source_name: str
    retrieved_at: datetime
    published_at: datetime
    fiscal_period: str | None = None
    reported_currency: str
    data_mode: DataMode
    confidence: float = Field(ge=0, le=1)
    provenance: str


class MetricPoint(BaseModel):
    name: str
    label: str
    value: float
    unit: str
    period: str
    provenance: Provenance


class FinancialPeriod(BaseModel):
    period: str
    revenue: float
    operating_income: float
    free_cash_flow: float
    roic: float
    currency: str
    unit: str = "million"
    accounting_standard: str
    fiscal_year_end: str


class ValuationScenario(BaseModel):
    name: str
    probability: float = Field(ge=0, le=1)
    growth_rate: float
    operating_margin: float
    discount_rate: float
    terminal_growth: float
    value_per_share: float
    currency: str
    rationale: str


class Evidence(BaseModel):
    title: str
    claim: str
    source_url: HttpUrl
    source_name: str
    published_at: datetime
    data_mode: DataMode


class AgentResult(BaseModel):
    agent_id: str
    display_name: str
    methodology: str
    thesis: str
    verdict: str
    score: int = Field(ge=0, le=100)
    facts: list[str]
    inferences: list[str]
    opinions: list[str]
    evidence: list[Evidence]
    valuation: str | None = None
    assumptions: list[str]
    catalysts: list[str]
    risks: list[str]
    invalidation_conditions: list[str]
    confidence: float = Field(ge=0, le=1)
    disagreements: list[str]
    missing_data: list[str]


class DebateTurn(BaseModel):
    sequence: int
    agent_id: str
    agent_name: str
    kind: str
    statement: str
    challenges_agent_id: str | None = None
    evidence_ids: list[int] = []


class Vote(BaseModel):
    agent_id: str
    verdict: str
    score: int
    weight: float


class FxRate(BaseModel):
    base: str
    quote: str
    rate: float
    as_of: date
    source_name: str
    source_url: HttpUrl
    data_mode: DataMode


class AnalysisRequest(BaseModel):
    asset_id: str
    base_currency: str = "USD"
    locale: str = "zh-CN"

    @field_validator("asset_id")
    @classmethod
    def validate_asset_id(cls, value: str) -> str:
        if ":" not in value:
            raise ValueError("asset_id must use MIC:symbol; ticker alone is ambiguous")
        return value


class AnalysisReport(BaseModel):
    report_id: str
    analysis_date: date
    asset: AssetIdentity
    data_mode: DataMode
    as_of: datetime
    source_summary: list[str]
    company_summary: str
    industry_summary: str
    accounting_note: str
    market_price: MetricPoint
    financials: list[FinancialPeriod]
    scenarios: list[ValuationScenario]
    fx_rate: FxRate | None
    base_currency: str
    converted_scenarios: list[ValuationScenario]
    sensitivity: dict[str, list[float]]
    agents: list[AgentResult]
    debate: list[DebateTurn]
    votes: list[Vote]
    consensus: str
    consensus_score: int
    llm_provider: str
    chair_synthesis: str
    major_disagreements: list[str]
    catalysts: list[str]
    risks: list[str]
    invalidation_conditions: list[str]
    missing_data: list[str]
    evidence: list[Evidence]
    disclaimer: str


class SearchResult(BaseModel):
    asset_id: str
    asset: AssetIdentity
    match_reason: str


class HealthResponse(BaseModel):
    status: str
    data_provider: str
    llm_provider: str
    database: str
