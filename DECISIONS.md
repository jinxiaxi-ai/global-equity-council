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
