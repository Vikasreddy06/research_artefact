# Evaluation analysis

**N/A** means the metric is not applicable or was not computed. A recorded 0 is a measured zero.

- Source: **AWS measurement**
- Run: 2026-10-23T12:17:38+00:00, 9000 requests, 24000 invocations, workers: 900
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
| requests with no business mutation | 1 |
| requests where stream and self-report disagree | 0 |
| final deliveries that were cold starts | 5788 |
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
| P1 | 1 | 1 | 1 | 1 | **N/A** | 1487 | 1415 | 1561 | 1487 | 1415 | 1561 | 2748 | 2608 | 2796 | 165.6 | 0.579 | 188.4 |
| P1 | 2 | 2 | 2 | 2 | **N/A** | 1662 | 1592 | 1733 | 5074 | 5003 | 5146 | 2509 | 2490 | 2527 | 61.89 | 0.683 | 208.5 |
| P1 | 5 | 5 | 5 | 5 | **N/A** | 1623 | 1550 | 1692 | 1.538e+04 | 1.53e+04 | 1.546e+04 | 2487 | 2468 | 2497 | 60.87 | 0.668 | 204 |
| P2 | 1 | 1 | 1 | 1 | 0 | 1454 | 1378 | 1529 | 1454 | 1378 | 1529 | 2783 | 2711 | 2832 | 127 | 0.566 | 183.1 |
| P2 | 2 | 2 | 2 | 2 | 1 | 1638 | 1566 | 1705 | 5045 | 4972 | 5116 | 2530 | 2517 | 2549 | 75.14 | 0.663 | 205.1 |
| P2 | 5 | 5 | 5 | 5 | 4 | 1666 | 1599 | 1732 | 1.542e+04 | 1.534e+04 | 1.55e+04 | 2527 | 2516 | 2533 | 69.84 | 0.678 | 208.5 |
| P3 | 1 | 3 | 3 | 3 | 0 | 1561 | 1488 | 1636 | 1561 | 1488 | 1636 | 2847 | 2804 | 2896 | 189.8 | 0.585 | 263.2 |
| P3 | 2 | 4 | 4 | 4 | 1 | 1683 | 1614 | 1752 | 5075 | 5005 | 5145 | 2548 | 2536 | 2568 | 76.8 | 0.679 | 211.3 |
| P3 | 5 | 7 | 7 | 7 | 4 | 1692 | 1620 | 1758 | 1.542e+04 | 1.534e+04 | 1.549e+04 | 2526 | 2514 | 2535 | 74.51 | 0.687 | 212.7 |

### Latency tests (9 tests, Holm-Bonferroni within this family)

| multiplicity | comparison | test | estimate | diff | ci_lo | ci_hi | effect_name | effect | p | p_holm | reject_h0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -0.935 | -5.413 | 3.068 | rank_biserial | -0.01253 | 0.6276 | 0.6276 | False |
| 1 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -75.35 | -80.61 | -68.47 | rank_biserial | -0.3257 | 1.81e-36 | 1.448e-35 | True |
| 1 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -73.95 | -79.47 | -67.01 | rank_biserial | -0.3267 | 1.148e-36 | 1.033e-35 | True |
| 2 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -17.27 | -22.5 | -10.61 | rank_biserial | -0.1335 | 2.347e-07 | 9.387e-07 | True |
| 2 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -23.69 | -31.69 | -17.62 | rank_biserial | -0.1799 | 3.242e-12 | 1.945e-11 | True |
| 2 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -6.884 | -14.72 | -0.197 | rank_biserial | -0.05244 | 0.04232 | 0.1269 | False |
| 5 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -19.33 | -24.65 | -13.76 | rank_biserial | -0.1693 | 5.508e-11 | 2.754e-10 | True |
| 5 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -25.14 | -32.48 | -19.32 | rank_biserial | -0.207 | 1.089e-15 | 7.621e-15 | True |
| 5 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -5.028 | -12.2 | 0.629 | rank_biserial | -0.0443 | 0.08633 | 0.1727 | False |

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
