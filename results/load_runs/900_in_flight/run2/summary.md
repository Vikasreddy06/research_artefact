# Evaluation analysis

**N/A** means the metric is not applicable or was not computed. A recorded 0 is a measured zero.

- Source: **AWS measurement**
- Run: 2026-10-30T03:39:01+00:00, 9000 requests, 24000 invocations, workers: 900
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
| final deliveries that were cold starts | 5827 |
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
| P1 | 1 | 1 | 1 | 1 | **N/A** | 1531 | 1456 | 1602 | 1531 | 1456 | 1602 | 2854 | 2805 | 2873 | 112.4 | 0.596 | 194 |
| P1 | 2 | 2 | 2 | 2 | **N/A** | 1630 | 1561 | 1699 | 5044 | 4976 | 5114 | 2547 | 2530 | 2560 | 61.63 | 0.658 | 206.2 |
| P1 | 5 | 5 | 5 | 5 | **N/A** | 1762 | 1696 | 1830 | 1.553e+04 | 1.545e+04 | 1.56e+04 | 2532 | 2522 | 2544 | 60.78 | 0.717 | 222.1 |
| P2 | 1 | 1 | 1 | 1 | 0 | 1571 | 1498 | 1642 | 1571 | 1498 | 1642 | 2842 | 2713 | 2873 | 183.8 | 0.603 | 200.1 |
| P2 | 2 | 2 | 2 | 2 | 1 | 1686 | 1613 | 1754 | 5104 | 5029 | 5172 | 2585 | 2567 | 2606 | 75.22 | 0.672 | 212.6 |
| P2 | 5 | 5 | 5 | 5 | 4 | 1675 | 1607 | 1742 | 1.542e+04 | 1.534e+04 | 1.55e+04 | 2553 | 2545 | 2562 | 71.84 | 0.672 | 211.6 |
| P3 | 1 | 3 | 3 | 3 | 0 | 1517 | 1440 | 1588 | 1517 | 1440 | 1588 | 2910 | 2761 | 2968 | 207.8 | 0.555 | 261.2 |
| P3 | 2 | 4 | 4 | 4 | 1 | 1690 | 1618 | 1756 | 5091 | 5020 | 5160 | 2587 | 2569 | 2606 | 77.57 | 0.673 | 215 |
| P3 | 5 | 7 | 7 | 7 | 4 | 1700 | 1634 | 1770 | 1.545e+04 | 1.537e+04 | 1.553e+04 | 2563 | 2548 | 2574 | 75.8 | 0.681 | 216.1 |

### Latency tests (9 tests, Holm-Bonferroni within this family)

| multiplicity | comparison | test | estimate | diff | ci_lo | ci_hi | effect_name | effect | p | p_holm | reject_h0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -0.961 | -5.63 | 3.185 | rank_biserial | -0.01318 | 0.6098 | 1 | False |
| 1 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -72.79 | -78.68 | -64.61 | rank_biserial | -0.2633 | 2.079e-24 | 1.871e-23 | True |
| 1 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -71.54 | -77.66 | -63.59 | rank_biserial | -0.2617 | 3.955e-24 | 3.164e-23 | True |
| 2 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -20.36 | -27.38 | -14.26 | rank_biserial | -0.1541 | 2.408e-09 | 1.445e-08 | True |
| 2 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -22.65 | -30.57 | -16.93 | rank_biserial | -0.1709 | 3.703e-11 | 2.592e-10 | True |
| 2 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -1.987 | -9.508 | 4.253 | rank_biserial | -0.01736 | 0.5016 | 1 | False |
| 5 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -12.13 | -18.67 | -4.914 | rank_biserial | -0.09592 | 0.0002041 | 0.0008164 | True |
| 5 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -17.84 | -23.67 | -10.36 | rank_biserial | -0.1284 | 6.675e-07 | 3.338e-06 | True |
| 5 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -4.308 | -12.39 | 1.337 | rank_biserial | -0.03768 | 0.1446 | 0.4339 | False |

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
