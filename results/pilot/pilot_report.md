# Pilot report

- Source: **AWS measurement**
- Pilot run: 2026-10-10T13:31:09+00:00, 150 requests, 300 invocations, multiplicity 2

## Rule (fixed before the pilot)

- duplicate-mutation rate: 95 % Wilson interval no wider than +-1.0 pp
- capacity per request: 95 % CI half-width at most 5 % of the mean
- N = largest requirement; at least the configured size 1000; at most 2499 (invocation budget 60000)

## Pilot estimates and required N

| path | metric | pilot_n | mean | sd | target | required_n | conservative_n |
|---|---|---|---|---|---|---|---|
| P1 | duplicate rate | 50 | 1 | 0 | +-1.0 pp | 189 | 2546 |
| P1 | capacity | 50 | 2 | 0 | +-5 % of mean | 1 | 1 |
| P2 | duplicate rate | 50 | 0 | 0 | +-1.0 pp | 189 | 2546 |
| P2 | capacity | 50 | 2 | 0 | +-5 % of mean | 1 | 1 |
| P3 | duplicate rate | 50 | 0 | 0 | +-1.0 pp | 189 | 2546 |
| P3 | capacity | 50 | 4 | 0 | +-5 % of mean | 1 | 1 |

`conservative_n` uses the pessimistic end of the pilot's own 95 % interval. The decision uses `required_n`.

## Decision

**N = 1000 requests per path per multiplicity** - the configured size meets the pilot requirement (largest requirement 189 <= 1000). Binding requirement: P1 duplicate rate (189).
