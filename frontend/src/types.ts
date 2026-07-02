export type DataMode = "live" | "cached" | "fixture";

export interface AssetIdentity {
  symbol: string;
  display_name: string;
  exchange: string;
  mic: string;
  country: string;
  security_type: string;
  trading_currency: string;
  reporting_currency: string;
  timezone: string;
  locale: string;
  isin?: string;
  provider_symbols: Record<string, string>;
  primary_listing: boolean;
}

export interface SearchResult {
  asset_id: string;
  asset: AssetIdentity;
  match_reason: string;
}

export interface Evidence {
  title: string;
  claim: string;
  source_url: string;
  source_name: string;
  published_at: string;
  data_mode: DataMode;
}

export interface FinancialPeriod {
  period: string;
  revenue: number;
  operating_income: number;
  free_cash_flow: number;
  roic: number;
  currency: string;
  unit: string;
  accounting_standard: string;
  fiscal_year_end: string;
}

export interface ValuationScenario {
  name: "Bear" | "Base" | "Bull";
  probability: number;
  growth_rate: number;
  operating_margin: number;
  discount_rate: number;
  terminal_growth: number;
  value_per_share: number;
  currency: string;
  rationale: string;
}

export interface AgentResult {
  agent_id: string;
  display_name: string;
  methodology: string;
  thesis: string;
  verdict: string;
  score: number;
  facts: string[];
  inferences: string[];
  opinions: string[];
  evidence: Evidence[];
  valuation?: string;
  assumptions: string[];
  catalysts: string[];
  risks: string[];
  invalidation_conditions: string[];
  confidence: number;
  disagreements: string[];
  missing_data: string[];
}

export interface DebateTurn {
  sequence: number;
  agent_id: string;
  agent_name: string;
  kind: string;
  statement: string;
  challenges_agent_id?: string;
  evidence_ids: number[];
}

export interface AnalysisReport {
  report_id: string;
  analysis_date: string;
  asset: AssetIdentity;
  data_mode: DataMode;
  as_of: string;
  source_summary: string[];
  company_summary: string;
  industry_summary: string;
  accounting_note: string;
  market_price: {
    value: number;
    unit: string;
    period: string;
    provenance: {
      source_url: string;
      source_name: string;
      retrieved_at: string;
      published_at: string;
      fiscal_period?: string;
      reported_currency: string;
      data_mode: DataMode;
      confidence: number;
      provenance: string;
    };
  };
  financials: FinancialPeriod[];
  scenarios: ValuationScenario[];
  fx_rate?: {
    base: string;
    quote: string;
    rate: number;
    as_of: string;
    source_name: string;
    source_url: string;
    data_mode: DataMode;
  };
  base_currency: string;
  converted_scenarios: ValuationScenario[];
  sensitivity: Record<string, number[]>;
  agents: AgentResult[];
  debate: DebateTurn[];
  votes: { agent_id: string; verdict: string; score: number; weight: number }[];
  consensus: string;
  consensus_score: number;
  llm_provider: string;
  chair_synthesis: string;
  major_disagreements: string[];
  catalysts: string[];
  risks: string[];
  invalidation_conditions: string[];
  missing_data: string[];
  evidence: Evidence[];
  disclaimer: string;
}
