# Evaluation analysis

**N/A** means the metric is not applicable or was not computed. A recorded 0 is a measured zero.

- Source: **AWS measurement**
- Run: 2026-10-22T15:23:46+00:00, 9000 requests, 24000 invocations, workers: 100
- alpha = 0.05, bootstrap B = 2000, seed = 0

## Data checks

| check | value |
|---|---|
| planned deliveries | 24000 |
| observed deliveries | 24000 |
| missing deliveries | 0 |
| deliveries with status error | 0 |
| after-commit injections that did not time out | 0 |
| deliveries with no function record (no capacity) | 1 |
| requests with no business mutation | 0 |
| requests where stream and self-report disagree | 0 |
| final deliveries that were cold starts | 5887 |
| mutation ground truth | stream |

## Duplicate mutation per injected retry (95 % Wilson and cluster-bootstrap CIs)

| path | multiplicity | requests | injected_retries | dup_mutations | dup_rate | dup_ci_lo | dup_ci_hi | dup_cluster_ci_lo | dup_cluster_ci_hi | dup_request_share | dup_request_ci_lo | dup_request_ci_hi | ccf_per_retry | successful_retry_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 1 | 1000 | 0 | 0 | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** |
| P1 | 2 | 1000 | 1000 | 1000 | 1 | 0.9962 | 1 | 1 | 1 | 1 | 0.9962 | 1 | **N/A** | 0 |
| P1 | 5 | 1000 | 4000 | 3999 | 0.9998 | 0.9986 | 1 | 0.999 | 1 | 1 | 0.9962 | 1 | **N/A** | 0.00025 |
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
| 5 | P1 vs P2 | one-sided (P1 higher) | 0.9998 | 0 | 0.9998 | 0.9982 | 1 | 89.42 | 0 | 0 | True |
| 5 | P1 vs P3 | one-sided (P1 higher) | 0.9998 | 0 | 0.9998 | 0.9982 | 1 | 89.42 | 0 | 0 | True |
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
| P1 | 1 | 1 | 1 | 1 | **N/A** | 638.8 | 577.2 | 703.6 | 638.8 | 577.2 | 703.6 | 2503 | 2487 | 2516 | 65.45 | 0.24 | 89.35 |
| P1 | 2 | 2 | 2 | 2 | **N/A** | 2119 | 2067 | 2170 | 5312 | 5259 | 5367 | 2562 | 2543 | 2571 | 60.96 | 0.863 | 261.6 |
| P1 | 5 | 4.999 | 4.996 | 5 | **N/A** | 2158 | 2109 | 2207 | 1.603e+04 | 1.598e+04 | 1.609e+04 | 2560 | 2546 | 2563 | 59.2 | 0.878 | 266.4 |
| P2 | 1 | 1 | 1 | 1 | 0 | 602.4 | 540.1 | 664.1 | 602.4 | 540.1 | 664.1 | 2507 | 2491 | 2519 | 63.75 | 0.225 | 84.71 |
| P2 | 2 | 2 | 2 | 2 | 1 | 2126 | 2073 | 2177 | 5311 | 5256 | 5367 | 2582 | 2573 | 2598 | 72.25 | 0.856 | 263 |
| P2 | 5 | 5 | 5 | 5 | 4 | 2115 | 2061 | 2167 | 1.597e+04 | 1.59e+04 | 1.603e+04 | 2583 | 2569 | 2591 | 69.94 | 0.855 | 261.5 |
| P3 | 1 | 3 | 3 | 3 | 0 | 686.2 | 624.3 | 750.5 | 686.2 | 624.3 | 750.5 | 2571 | 2558 | 2585 | 137.6 | 0.23 | 159.8 |
| P3 | 2 | 4 | 4 | 4 | 1 | 2175 | 2124 | 2223 | 5377 | 5323 | 5429 | 2589 | 2581 | 2602 | 73.22 | 0.876 | 269.2 |
| P3 | 5 | 7 | 7 | 7 | 4 | 2147 | 2096 | 2196 | 1.602e+04 | 1.596e+04 | 1.608e+04 | 2582 | 2573 | 2601 | 73.36 | 0.864 | 265.7 |

### Latency tests (9 tests, Holm-Bonferroni within this family)

| multiplicity | comparison | test | estimate | diff | ci_lo | ci_hi | effect_name | effect | p | p_holm | reject_h0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | 0.131 | -0.186 | 0.467 | rank_biserial | 0.02076 | 0.4216 | 0.5206 | False |
| 1 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -77.59 | -78.72 | -75.63 | rank_biserial | -0.5864 | 3.96e-114 | 3.168e-113 | True |
| 1 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -78.23 | -79.02 | -76.59 | rank_biserial | -0.6142 | 4.93e-125 | 4.437e-124 | True |
| 2 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -21.49 | -29.64 | -16.15 | rank_biserial | -0.1626 | 3.074e-10 | 1.537e-09 | True |
| 2 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -26.94 | -34.45 | -20.04 | rank_biserial | -0.1949 | 4.469e-14 | 3.128e-13 | True |
| 2 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -3.099 | -11.36 | 2.225 | rank_biserial | -0.02907 | 0.2603 | 0.5206 | False |
| 5 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -13.96 | -20.21 | -6.814 | rank_biserial | -0.1023 | 7.478e-05 | 0.0002991 | True |
| 5 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -25.61 | -32.86 | -19.41 | rank_biserial | -0.1888 | 2.633e-13 | 1.58e-12 | True |
| 5 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -11.74 | -19.36 | -4.426 | rank_biserial | -0.08586 | 0.000886 | 0.002658 | True |

## Expectations stated before the runs (E1-E3)

| expectation | multiplicity | subject | estimate | ci_lo | ci_hi | p | rule | decision |
|---|---|---|---|---|---|---|---|---|
| E1 | 2 | P1 duplicate rate | 1 | 0.9962 | 1 | 9.333e-302 | Wilson and cluster-bootstrap lower bounds > 0.5 | supported |
| E1 | 5 | P1 duplicate rate | 0.9998 | 0.9986 | 1 | 0 | Wilson and cluster-bootstrap lower bounds > 0.5 | supported |
| E2 | 2 | P2 reduction vs P1 | 1 | 0.992 | 1 | **N/A** | lower bound of the relative reduction > 0.90 | supported |
| E2 | 2 | P3 reduction vs P1 | 1 | 0.992 | 1 | **N/A** | lower bound of the relative reduction > 0.90 | supported |
| E2 | 5 | P2 reduction vs P1 | 1 | 0.998 | 1 | **N/A** | lower bound of the relative reduction > 0.90 | supported |
| E2 | 5 | P3 reduction vs P1 | 1 | 0.998 | 1 | **N/A** | lower bound of the relative reduction > 0.90 | supported |
| E3 | 1 | P3 - P2 capacity per request | 2 | **N/A** | **N/A** | **N/A** | reported as a count, not tested | reported, not tested |
| E3 | 2 | P3 - P2 capacity per request | 2 | **N/A** | **N/A** | **N/A** | reported as a count, not tested | reported, not tested |
| E3 | 5 | P3 - P2 capacity per request | 2 | **N/A** | **N/A** | **N/A** | reported as a count, not tested | reported, not tested |

## Sensitivity: timeout after P3's business-item write

Not part of these runs.
