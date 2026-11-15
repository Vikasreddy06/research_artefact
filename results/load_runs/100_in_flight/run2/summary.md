# Evaluation analysis

**N/A** means the metric is not applicable or was not computed. A recorded 0 is a measured zero.

- Source: **AWS measurement**
- Run: 2026-10-22T15:35:30+00:00, 9000 requests, 24000 invocations, workers: 100
- alpha = 0.05, bootstrap B = 2000, seed = 0

## Data checks

| check | value |
|---|---|
| planned deliveries | 24000 |
| observed deliveries | 24000 |
| missing deliveries | 0 |
| deliveries with status error | 0 |
| after-commit injections that did not time out | 0 |
| deliveries with no function record (no capacity) | 0 |
| requests with no business mutation | 0 |
| requests where stream and self-report disagree | 0 |
| final deliveries that were cold starts | 5884 |
| mutation ground truth | stream |

## Duplicate mutation per injected retry (95 % Wilson and cluster-bootstrap CIs)

| path | multiplicity | requests | injected_retries | dup_mutations | dup_rate | dup_ci_lo | dup_ci_hi | dup_cluster_ci_lo | dup_cluster_ci_hi | dup_request_share | dup_request_ci_lo | dup_request_ci_hi | ccf_per_retry | successful_retry_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 1 | 1000 | 0 | 0 | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** |
| P1 | 2 | 1000 | 1000 | 1000 | 1 | 0.9962 | 1 | 1 | 1 | 1 | 0.9962 | 1 | **N/A** | 0 |
| P1 | 5 | 1000 | 4000 | 4000 | 1 | 0.999 | 1 | 1 | 1 | 1 | 0.9962 | 1 | **N/A** | 0 |
| P2 | 1 | 1000 | 0 | 0 | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** |
| P2 | 2 | 1000 | 1000 | 0 | 0 | 0 | 0.003827 | 0 | 0 | 0 | 0 | 0.003827 | 1 | 1 |
| P2 | 5 | 1000 | 4000 | 0 | 0 | 0 | 0.0009594 | 0 | 0 | 0 | 0 | 0.003827 | 1 | 1 |
| P3 | 1 | 1000 | 0 | 0 | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** |
| P3 | 2 | 1000 | 1000 | 0 | 0 | 0 | 0.003827 | 0 | 0 | 0 | 0 | 0.003827 | 1 | 1 |
| P3 | 5 | 1000 | 4000 | 0 | 0 | 0 | 0.0009594 | 0 | 0 | 0 | 0 | 0.003827 | 1 | 1 |

### Two-proportion z-tests (4 one-sided and 2 exploratory tests, Holm-Bonferroni within each group)

| multiplicity | comparison | alternative | rate_a | rate_b | diff | ci_lo | ci_hi | z | p | p_holm | reject_h0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | P1 vs P2 | one-sided (P1 higher) | 1 | 0 | 1 | 0.9946 | 1 | 44.72 | 0 | 0 | True |
| 2 | P1 vs P3 | one-sided (P1 higher) | 1 | 0 | 1 | 0.9946 | 1 | 44.72 | 0 | 0 | True |
| 2 | P2 vs P3 | two-sided (exploratory) | 0 | 0 | 0 | -0.003827 | 0.003827 | **N/A** | **N/A** | **N/A** | False |
| 5 | P1 vs P2 | one-sided (P1 higher) | 1 | 0 | 1 | 0.9986 | 1 | 89.44 | 0 | 0 | True |
| 5 | P1 vs P3 | one-sided (P1 higher) | 1 | 0 | 1 | 0.9986 | 1 | 89.44 | 0 | 0 | True |
| 5 | P2 vs P3 | two-sided (exploratory) | 0 | 0 | 0 | -0.0009594 | 0.0009594 | **N/A** | **N/A** | **N/A** | False |

### Chi-square, duplicate yes/no by cell

| table | cells | chi2 | p | dof | min_expected | note |
|---|---|---|---|---|---|---|
| path x multiplicity | 6 | 1.5e+04 | 0 | 5 | 333.3 |  |
| paths at multiplicity 2 | 3 | 3000 | 0 | 2 | 333.3 |  |
| paths at multiplicity 5 | 3 | 1.2e+04 | 0 | 2 | 1333 |  |

## Capacity and latency per request (95 % bootstrap CIs)

`latency_mean_ms` is the final invocation only. `e2e_mean_ms` sums every delivery's client round trip, including injected timeouts.

| path | multiplicity | capacity_mean | capacity_mean_ci_lo | capacity_mean_ci_hi | capacity_rule_mean | latency_mean_ms | latency_mean_ms_ci_lo | latency_mean_ms_ci_hi | e2e_mean_ms | e2e_mean_ms_ci_lo | e2e_mean_ms_ci_hi | latency_p95_ms | latency_p95_ms_ci_lo | latency_p95_ms_ci_hi | latency_warm_mean_ms | cold_final_share | ddb_mean_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 1 | 1 | 1 | 1 | **N/A** | 639 | 575.5 | 702 | 639 | 575.5 | 702 | 2487 | 2476 | 2503 | 60.14 | 0.243 | 87.27 |
| P1 | 2 | 2 | 2 | 2 | **N/A** | 2089 | 2035 | 2140 | 5289 | 5235 | 5343 | 2550 | 2542 | 2565 | 61.67 | 0.853 | 258.5 |
| P1 | 5 | 5 | 5 | 5 | **N/A** | 2128 | 2077 | 2177 | 1.6e+04 | 1.594e+04 | 1.605e+04 | 2561 | 2542 | 2569 | 62.78 | 0.868 | 262.7 |
| P2 | 1 | 1 | 1 | 1 | 0 | 632.8 | 574.3 | 695.4 | 632.8 | 574.3 | 695.4 | 2489 | 2474 | 2513 | 61.55 | 0.24 | 87.03 |
| P2 | 2 | 2 | 2 | 2 | 1 | 2161 | 2111 | 2209 | 5354 | 5301 | 5405 | 2576 | 2562 | 2584 | 72.7 | 0.872 | 266.7 |
| P2 | 5 | 5 | 5 | 5 | 4 | 2181 | 2133 | 2230 | 1.606e+04 | 1.6e+04 | 1.611e+04 | 2586 | 2571 | 2600 | 67.75 | 0.88 | 269.1 |
| P3 | 1 | 3 | 3 | 3 | 0 | 676 | 612.1 | 737.9 | 676 | 612.1 | 737.9 | 2566 | 2555 | 2580 | 133.3 | 0.227 | 157 |
| P3 | 2 | 4 | 4 | 4 | 1 | 2131 | 2079 | 2181 | 5319 | 5264 | 5372 | 2585 | 2577 | 2600 | 71.64 | 0.858 | 264.2 |
| P3 | 5 | 7 | 7 | 7 | 4 | 2093 | 2038 | 2147 | 1.596e+04 | 1.589e+04 | 1.602e+04 | 2582 | 2565 | 2591 | 74.71 | 0.843 | 259.8 |

### Latency tests (9 tests, Holm-Bonferroni within this family)

| multiplicity | comparison | test | estimate | diff | ci_lo | ci_hi | effect_name | effect | p | p_holm | reject_h0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -0.12 | -0.45 | 0.205 | rank_biserial | -0.01882 | 0.4662 | 0.9323 | False |
| 1 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -78.03 | -78.95 | -76.05 | rank_biserial | -0.5984 | 9.226e-119 | 8.303e-118 | True |
| 1 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -77.38 | -78.62 | -75 | rank_biserial | -0.5935 | 7.081e-117 | 5.665e-116 | True |
| 2 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -31.44 | -38.94 | -24.4 | rank_biserial | -0.2423 | 6.556e-21 | 3.934e-20 | True |
| 2 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -33.79 | -40.13 | -26.67 | rank_biserial | -0.2493 | 4.797e-22 | 3.358e-21 | True |
| 2 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -1.062 | -8.237 | 3.961 | rank_biserial | -0.01518 | 0.5568 | 0.9323 | False |
| 5 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -27.6 | -34.35 | -20.58 | rank_biserial | -0.2144 | 1.038e-16 | 5.19e-16 | True |
| 5 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -21.84 | -29.23 | -16.88 | rank_biserial | -0.1701 | 4.539e-11 | 1.816e-10 | True |
| 5 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | 3.955 | -1.319 | 11.39 | rank_biserial | 0.034 | 0.188 | 0.564 | False |

## Expectations stated before the runs (E1-E3)

| expectation | multiplicity | subject | estimate | ci_lo | ci_hi | p | rule | decision |
|---|---|---|---|---|---|---|---|---|
| E1 | 2 | P1 duplicate rate | 1 | 0.9962 | 1 | 9.333e-302 | Wilson and cluster-bootstrap lower bounds > 0.5 | supported |
| E1 | 5 | P1 duplicate rate | 1 | 0.999 | 1 | 0 | Wilson and cluster-bootstrap lower bounds > 0.5 | supported |
| E2 | 2 | P2 reduction vs P1 | 1 | 0.992 | 1 | **N/A** | lower bound of the relative reduction > 0.90 | supported |
| E2 | 2 | P3 reduction vs P1 | 1 | 0.992 | 1 | **N/A** | lower bound of the relative reduction > 0.90 | supported |
| E2 | 5 | P2 reduction vs P1 | 1 | 0.998 | 1 | **N/A** | lower bound of the relative reduction > 0.90 | supported |
| E2 | 5 | P3 reduction vs P1 | 1 | 0.998 | 1 | **N/A** | lower bound of the relative reduction > 0.90 | supported |
| E3 | 1 | P3 - P2 capacity per request | 2 | **N/A** | **N/A** | **N/A** | reported as a count, not tested | reported, not tested |
| E3 | 2 | P3 - P2 capacity per request | 2 | **N/A** | **N/A** | **N/A** | reported as a count, not tested | reported, not tested |
| E3 | 5 | P3 - P2 capacity per request | 2 | **N/A** | **N/A** | **N/A** | reported as a count, not tested | reported, not tested |

## Sensitivity: timeout after P3's business-item write

Not part of these runs.
