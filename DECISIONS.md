# Architecture Decision Log

## 2026-07-02 — Offline-first vertical slice

- Use a React/Vite TypeScript frontend and FastAPI/Pydantic backend. This keeps
  schemas explicit and makes the demo deployable as two small containers.
- Treat `(symbol, MIC)` as the canonical public asset key and expose a stable
  `asset_id` (`MIC:symbol`). Ticker alone is never used as identity.
- Make deterministic fixtures the default, with explicit `fixture` provenance.
  Live adapters remain opt-in so the five-market acceptance suite is repeatable
  without credentials or network availability.
- Use SVG for charts and share-card export. It stays crisp, dependency-light,
  themeable, and accessible through adjacent text summaries.
- Use a restrained editorial-finance visual system: deep navy surfaces, teal
  action color, amber caveats, tabular figures, generous whitespace, and
  semantic tokens in paired light/dark themes.
- The installed `ui-ux-pro-max` skill contains pointer files for its `scripts`
  and `data` directories rather than the referenced resources, so its required
  design-system generator could not run. Its accessibility, interaction,
  responsive, theming, and chart guidance is applied directly and verified in
  browser tests.
- Use repository-local npm cache for verification when the host user's global
  cache contains root-owned legacy entries. This avoids requiring privileged
  system changes and does not affect project behavior.
- Keep the deterministic committee explainable: every score is derived from
  fixture metrics and declared methodology weights. The demo LLM provider adds
  no random text and never fabricates source material.
- Limit the LLM's role to the committee-chair synthesis over an already
  validated payload. Scores, facts, valuation inputs, and evidence remain
  deterministic and schema-controlled; selecting OpenAI changes the synthesis
  provider, not the source of truth.
- Implement the provider cache contract for both SQLite and PostgreSQL. SQLite
  remains zero-setup; PostgreSQL uses psycopg and the same TTL semantics.

## 2026-07-02 — Post-publish usability fixes

- Language switching must affect generated research content, not only static UI
  chrome. The backend now receives `locale` and localizes deterministic report
  fields, chair synthesis, scenarios, debate turns, risks, and disclaimers.
- Expand the credential-free fixture universe for user-requested US tickers
  `MU` and `AAOI`. Keep the same `MIC:symbol` identity rule and attach SEC/market
  provenance so search results can flow into the same analysis pipeline.

## 2026-07-02 — Fixture freshness disclosure

- Do not relabel fixed fixture prices as current data. When the market price is
  fixture-backed, the UI now calls it a snapshot price and shows a visible
  freshness warning with the price snapshot date and latest filing date.
- Current market prices require a licensed or authenticated market-data provider.
  The public demo remains no-key and deterministic; production deployments
  should wire a real quote provider instead of silently pretending fixtures are
  live.

## 2026-07-02 — Bring Your Own Key market data

- Follow the common GitHub open-source pattern: users provide their own market
  data API key in `.env`; the repository never ships a shared production key.
- Keep keys server-side only. `MARKET_DATA_API_KEY`, `TWELVEDATA_API_KEY`, and
  `FINNHUB_API_KEY` are read by FastAPI, cached by the provider layer, and never
  exposed through Vite/browser environment variables.
- Implement live quote overlay providers for Twelve Data and Finnhub. They
  update the market-price datapoint and provenance while retaining fixture
  fundamentals unless a separate fundamentals adapter is configured later.
