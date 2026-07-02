# Contributing

Thanks for improving Global Equity Council.

## Setup

```bash
npm run install:all
npm run dev
```

Open <http://localhost:5173>. Demo mode requires no credentials.

## Quality gate

```bash
npm run check
npm --prefix frontend exec playwright install chromium
npm run test:e2e
```

Pull requests should add tests for changed provider contracts, schemas, or UI
flows. New markets must include a stable fixture, original source, MIC, local
timezone, accounting basis, and an explicit live-data fallback story.

By contributing you agree that your work is licensed under Apache-2.0.
