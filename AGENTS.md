# Working on Global Equity Council

1. Preserve provenance. Every new financial datum needs source, timestamps,
   currency, mode, confidence, and normalization notes.
2. Never identify a security by ticker alone. Use `MIC:symbol`.
3. Keep demo mode deterministic and credential-free.
4. Separate facts, inferences, and opinions in every agent result.
5. Run `npm run check` and `npm run test:e2e` before proposing a change.
6. Record consequential architecture or product tradeoffs in `DECISIONS.md`.
7. Do not add brokerage execution or personalized investment advice.
