# Evaluation analysis

**N/A** means the metric is not applicable or was not computed. A recorded 0 is a measured zero.

- Source: **AWS measurement**
- Run: 2026-10-12T02:28:43+00:00, 9000 requests, 24000 invocations, workers: 1
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
| final deliveries that were cold starts | 6001 |
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
| P1 | 1 | 1 | 1 | 1 | **N/A** | 62.77 | 62.05 | 63.43 | 62.77 | 62.05 | 63.43 | 79.94 | 79.76 | 80.19 | 62.77 | 0 | 20.36 |
| P1 | 2 | 2 | 2 | 2 | **N/A** | 2461 | 2457 | 2465 | 5520 | 5516 | 5524 | 2562 | 2554 | 2582 | **N/A** | 1 | 302.2 |
| P1 | 5 | 5 | 5 | 5 | **N/A** | 2466 | 2462 | 2470 | 1.647e+04 | 1.646e+04 | 1.648e+04 | 2563 | 2559 | 2570 | **N/A** | 1 | 302.6 |
| P2 | 1 | 1 | 1 | 1 | 0 | 63.55 | 62.83 | 64.32 | 63.55 | 62.83 | 64.32 | 80.31 | 79.96 | 81.4 | 63.55 | 0 | 20.78 |
| P2 | 2 | 2 | 2 | 2 | 1 | 2489 | 2485 | 2493 | 5547 | 5543 | 5551 | 2602 | 2585 | 2609 | **N/A** | 1 | 304.5 |
| P2 | 5 | 5 | 5 | 5 | 4 | 2488 | 2484 | 2492 | 1.647e+04 | 1.646e+04 | 1.648e+04 | 2599 | 2582 | 2609 | **N/A** | 1 | 304.9 |
| P3 | 1 | 3 | 3 | 3 | 0 | 139 | 136.2 | 144.2 | 139 | 136.2 | 144.2 | 160.6 | 160 | 162.6 | 137 | 0.001 | 93.27 |
| P3 | 2 | 4 | 4 | 4 | 1 | 2495 | 2491 | 2499 | 5554 | 5549 | 5558 | 2602 | 2585 | 2611 | **N/A** | 1 | 307.1 |
| P3 | 5 | 7 | 7 | 7 | 4 | 2497 | 2493 | 2501 | 1.649e+04 | 1.648e+04 | 1.65e+04 | 2602 | 2595 | 2611 | **N/A** | 1 | 306.5 |

### Latency tests (9 tests, Holm-Bonferroni within this family)

| multiplicity | comparison | test | estimate | diff | ci_lo | ci_hi | effect_name | effect | p | p_holm | reject_h0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -0.074 | -0.223 | 0.071 | rank_biserial | -0.02592 | 0.3156 | 0.3156 | False |
| 1 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -79.12 | -79.39 | -78.78 | rank_biserial | -0.9969 | 0 | 0 | True |
| 1 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -78.97 | -79.26 | -78.57 | rank_biserial | -0.9948 | 0 | 0 | True |
| 2 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -27.85 | -35.67 | -20.7 | rank_biserial | -0.2624 | 2.968e-24 | 1.484e-23 | True |
| 2 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -35.98 | -39.82 | -28.5 | rank_biserial | -0.3208 | 2e-35 | 1.4e-34 | True |
| 2 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -2.736 | -11.53 | -0.118 | rank_biserial | -0.05516 | 0.0327 | 0.0654 | False |
| 5 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -20.48 | -27.3 | -18.59 | rank_biserial | -0.2015 | 6.094e-15 | 2.437e-14 | True |
| 5 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -30.64 | -38.48 | -22.84 | rank_biserial | -0.2732 | 3.704e-26 | 2.223e-25 | True |
| 5 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -8.91 | -16.02 | -1.208 | rank_biserial | -0.08097 | 0.001718 | 0.005154 | True |

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

Source: AWS measurement. P3 only, timeout between the business write and marking the key COMPLETED.

| path | multiplicity | requests | injected_retries | dup_mutations | dup_rate | dup_ci_lo | dup_ci_hi | dup_cluster_ci_lo | dup_cluster_ci_hi | dup_request_share | dup_request_ci_lo | dup_request_ci_hi | ccf_per_retry | successful_retry_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P3 | 2 | 1000 | 1000 | 1000 | 1 | 0.9962 | 1 | 1 | 1 | 1 | 0.9962 | 1 | 0 | 0 |
| P3 | 5 | 1000 | 4000 | 4000 | 1 | 0.999 | 1 | 1 | 1 | 1 | 0.9962 | 1 | 0 | 0 |

| multiplicity | final_outcome | requests |
|---|---|---|
| 2 | APPLIED | 1000 |
| 5 | APPLIED | 1000 |
