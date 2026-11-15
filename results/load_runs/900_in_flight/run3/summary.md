# Evaluation analysis

**N/A** means the metric is not applicable or was not computed. A recorded 0 is a measured zero.

- Source: **AWS measurement**
- Run: 2026-10-30T03:41:04+00:00, 9000 requests, 24000 invocations, workers: 900
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
| final deliveries that were cold starts | 5673 |
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
| P1 | 1 | 1 | 1 | 1 | **N/A** | 1363 | 1291 | 1435 | 1363 | 1291 | 1435 | 2534 | 2522 | 2552 | 75.5 | 0.542 | 173.9 |
| P1 | 2 | 2 | 2 | 2 | **N/A** | 1630 | 1561 | 1703 | 5015 | 4944 | 5090 | 2534 | 2528 | 2545 | 63.66 | 0.658 | 206.3 |
| P1 | 5 | 5 | 5 | 5 | **N/A** | 1798 | 1732 | 1862 | 1.555e+04 | 1.548e+04 | 1.563e+04 | 2544 | 2526 | 2550 | 61.72 | 0.73 | 225.8 |
| P2 | 1 | 1 | 1 | 1 | 0 | 1317 | 1241 | 1393 | 1317 | 1241 | 1393 | 2543 | 2528 | 2549 | 73.58 | 0.524 | 168.5 |
| P2 | 2 | 2 | 2 | 2 | 1 | 1673 | 1603 | 1744 | 5041 | 4969 | 5113 | 2572 | 2558 | 2583 | 75.99 | 0.668 | 210.6 |
| P2 | 5 | 5 | 5 | 5 | 4 | 1696 | 1625 | 1767 | 1.542e+04 | 1.534e+04 | 1.551e+04 | 2562 | 2552 | 2575 | 73.56 | 0.678 | 214.1 |
| P3 | 1 | 3 | 3 | 3 | 0 | 1434 | 1357 | 1508 | 1434 | 1357 | 1508 | 2626 | 2608 | 2631 | 151.5 | 0.539 | 250.3 |
| P3 | 2 | 4 | 4 | 4 | 1 | 1654 | 1585 | 1723 | 5038 | 4965 | 5109 | 2568 | 2561 | 2578 | 77.78 | 0.658 | 209.8 |
| P3 | 5 | 7 | 7 | 7 | 4 | 1694 | 1625 | 1762 | 1.538e+04 | 1.53e+04 | 1.546e+04 | 2565 | 2555 | 2577 | 78.17 | 0.676 | 214.7 |

### Latency tests (9 tests, Holm-Bonferroni within this family)

| multiplicity | comparison | test | estimate | diff | ci_lo | ci_hi | effect_name | effect | p | p_holm | reject_h0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | 2.032 | -1.31 | 6.258 | rank_biserial | 0.03065 | 0.2353 | 0.7059 | False |
| 1 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -76.68 | -81.23 | -70.5 | rank_biserial | -0.3551 | 5.151e-43 | 4.121e-42 | True |
| 1 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -79.36 | -84.14 | -74.46 | rank_biserial | -0.3827 | 1.096e-49 | 9.867e-49 | True |
| 2 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -17.92 | -23.98 | -10.88 | rank_biserial | -0.1336 | 2.291e-07 | 1.374e-06 | True |
| 2 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -21.11 | -28.48 | -15.25 | rank_biserial | -0.1586 | 8.196e-10 | 5.737e-09 | True |
| 2 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -3.288 | -10.83 | 2.589 | rank_biserial | -0.02782 | 0.2814 | 0.7059 | False |
| 5 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -12.6 | -19.3 | -5.078 | rank_biserial | -0.09347 | 0.0002958 | 0.001183 | True |
| 5 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -16.62 | -22.91 | -8.759 | rank_biserial | -0.116 | 7.134e-06 | 3.567e-05 | True |
| 5 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -2.653 | -10.32 | 2.892 | rank_biserial | -0.02552 | 0.3231 | 0.7059 | False |

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
