# Acceptance Matrix

This file records reproducible evidence. It must be updated only from actual
commands or browser checks.

## Automated quality gate

Final release verification ran on 2026-07-02:

```bash
npm run check
npm run test:e2e
```

Observed results:

- Prettier and Ruff format checks: passed
- ESLint and Ruff lint: passed
- TypeScript and strict mypy: passed (9 Python source files)
- Pytest: 22 passed
- Vitest: 3 passed
- Vite production build: passed (228.98 kB JS / 71.41 kB gzip)
- Single-origin production serve: `/`, `/api/health`, and SAP analysis returned 200
- Secret scan: passed (58 files)
- Playwright: 3 passed, 3 intentionally project-skipped
- Live SEC adapter smoke test: latest AAPL 10-K returned in `live` mode
- Browser console warnings/errors during manual acceptance: 0
- 390 px mobile document overflow: 0 px

## Requirement mapping

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| One clear start command | root `npm run dev`; production `docker compose up --build` | dev command started both services; health and browser verified |
| Keyless five-market analysis | fixture provider + deterministic committee | provider parametrized tests + five-market browser flow passed |
| OpenAI switch | `LLMProvider`, `OpenAIProvider`, env configuration | LLM unit tests and documented config |
| Identity not ticker-only | immutable `AssetIdentity`, `MIC:symbol` request validation | ambiguity and 422 API tests |
| Provenance on critical data | `Provenance`, `Evidence`, dated `FxRate` schemas | contract/API tests + evidence UI |
| Investor methodologies | six weighted, explainable persona definitions | schema/methodology tests |
| Functional agents | verification, fundamentals, valuation, industry, macro/FX, red team, risk, chair | 14-agent schema test |
| Valuation/debate/vote | scenarios, assumptions, sensitivity, timeline, weighted vote | deterministic committee tests + UI |
| Bilingual/responsive/themes | React semantic UI and tokenized paired themes | Playwright desktop/mobile interactions |
| Share card | accessible dialog and deterministic SVG export | browser interaction test |
| SEC public source | identified, cached, rate-limited, retrying EDGAR adapter | live AAPL 10-K smoke test returned SEC URL |
| Global normalization | currency/reporting currency, accounting basis, FY end, units, dated FX, ADR identity | five-market contracts |
| Engineering files | README, LICENSE, NOTICE, CONTRIBUTING, SECURITY, decisions, roadmap, env, Docker, CI | repository inspection |
| No secrets/placeholders | environment-only credentials; scan script | `npm run check:secrets`, TODO scan |
| Production build | Vite TypeScript build and multi-stage container | `npm run build` passed; CI defines container build |

## Browser evidence

Screenshots are stored under `docs/screenshots/`:

- `desktop-aapl.png` — 1280×720 light desktop
- `mobile-tencent.png` — 390×844 mobile layout
- `share-card-sap.png` — dark-mode share card

The in-app browser manually verified AAPL, 600519.SS, 0700.HK, 7203.T, SAP.DE,
the SAP ADR ambiguity chooser, source links, local/reporting currency,
timezone/mode labels, Chinese/English, CNY conversion, light/dark mode, and the
share dialog. Playwright additionally fails on console errors, page errors, or
failed `/api/` requests.

Docker CLI and GitHub CLI were not installed in the release host. Container
build remains an explicit CI job; exact GitHub publication commands are in
`PUSH_COMMANDS.md`.
