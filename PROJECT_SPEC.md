# Global Equity Council — Project Specification

## 1. Product

Build an open-source, globally oriented AI investment-committee web
application. It performs research, valuation, debate, rebuttal, and voting; it
does not trade, connect to a broker, or provide investment advice. Unsupported
live markets must be explained and never fabricated.

## 2. Security identity

Ticker alone is forbidden as identity. `AssetIdentity` contains symbol,
display name, exchange, MIC, country, security type, trading/reporting
currencies, timezone, locale, optional ISIN, provider symbols, and
primary-listing status. Search supports ticker, exchange, and company name and
must offer a listing chooser for ambiguity.

## 3. Repeatable market coverage

The credential-free release verifies:

1. United States — AAPL
2. Mainland China — 600519.SS
3. Hong Kong — 0700.HK
4. Japan — 7203.T
5. Europe — SAP.DE

Each fixture is dated, sourced, and stable. Live data may replace a fixture only
through the same provider contract.

## 4. Provider architecture and provenance

Define adapters for asset search, market data, financial statements, regulatory
filings, corporate actions, news, macro data, and FX. Priority is local
regulator/exchange, issuer IR, trusted vendor, aggregator, then labeled fixture.
SEC EDGAR is fully implemented; other MVP markets have normalized primary-source
fixtures and replaceable interfaces.

Every critical record retains source URL/name, retrieval/publication times,
fiscal period, reported currency, `live|cached|fixture` mode, confidence, and
provenance. Implement cache, timeout, retry, rate limiting, fallback, and input
validation.

## 5. Global normalization

Preserve USD/CNY/HKD/JPY/EUR, original and base currencies, dated FX, GAAP/IFRS/
CAS differences, non-calendar fiscal years, units, corporate-action caveats,
local dates/timezones, and ADR/primary-listing differences. Do not hide
non-comparability.

## 6. Council

Investor-methodology agents:

- Buffett-inspired — moat, ROIC, free cash flow, capital allocation, safety
  margin
- Munger-inspired — quality, compounding, management, predictability
- Damodaran-inspired — narrative, DCF, capital cost, assumptions
- Peter Lynch-inspired — lifecycle, growth, PEG, understandability
- Cathie Wood-inspired — innovation, adoption, addressable market
- Burry-inspired — contrarian evidence, accounting anomalies, cycles

Functional agents: Data Verification, Fundamental Analysis, Valuation, Industry
and Competitive Analysis, Macro and Currency, Bear Case / Red Team, Risk
Manager, and Investment Committee Chair.

Every result strictly validates thesis, verdict, score, facts, inferences,
opinions, evidence, valuation, assumptions, catalysts, risks, invalidation
conditions, confidence, disagreements, and missing data. Inspired-by means
methodology, not impersonation or endorsement.

## 7. Analysis output

Generate company/industry summaries, trends, advantages/disadvantages,
bear/base/bull local and optional base-currency ranges, assumptions,
sensitivity, catalyst calendar, invalidation conditions, rebuttal timeline,
votes/consensus/disagreements, and the impact of data gaps. Never present a
simple model or LLM guess as precise valuation.

## 8. Experience

Deliver responsive global search, exact-listing selection, market/currency/
timezone/mode badges, debate timeline, charts, scenario comparison,
original-source links, risk/data-gap panels, Chinese/English, light/dark mode,
and share-card export. Share cards include market, exchange, analysis date,
data mode, and disclaimer.

## 9. Technology and quality

Use TypeScript web frontend, Python FastAPI backend, strict schemas, LLM
abstraction with OpenAI and a deterministic no-key provider, SQLite by default
with PostgreSQL support, Docker Compose, and one development start command.
Do not commit credentials or copied branding/code.

Ship AGENTS, README, LICENSE, NOTICE, CONTRIBUTING, SECURITY, DECISIONS, ROADMAP,
environment example, Dockerfile, Compose, and CI. Quality gates include
formatter, lint, type checking, unit tests, provider contracts, API integration,
agent schemas, deterministic fixtures, browser E2E, and secret scanning.

## 10. Completion criteria

- One clear command starts the whole project.
- All five demo markets complete without an API key.
- OpenAI is selectable when configured.
- Identity never relies on ticker alone.
- Critical data visibly includes source, time, currency, and mode.
- Format, lint, typecheck, tests, production build, and browser flows actually
  pass.
- No secrets, unexplained core TODOs, empty screens, or obvious placeholders.
- README covers architecture, coverage, sources, installation, configuration,
  screenshots, limits, roadmap, license, and disclaimer.
- Final screenshots live in `docs/screenshots`.
- A final commit is created; publish when GitHub CLI authentication is
  available, otherwise provide exact commands in `PUSH_COMMANDS.md`.

`docs/ACCEPTANCE.md` maps these criteria to repeatable verification evidence.
