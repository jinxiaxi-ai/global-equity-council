# Security Policy

## Reporting

Please report suspected vulnerabilities privately through GitHub Security
Advisories. Do not open a public issue for credential exposure, injection,
dependency compromise, or a route that could be abused.

## Current boundary

- The project does not execute trades or connect to brokers.
- Credentials are read only from environment variables.
- Demo mode is keyless, deterministic, validated, rate-limited, and read-only.
- CORS origins, upstream timeouts, SEC identification, and request limits are
  configurable.
- `npm run check:secrets` checks the repository for common credential formats.

No market-data or LLM response should be treated as trusted HTML. The UI renders
provider text as React text nodes and opens external sources with
`rel="noreferrer"`.
