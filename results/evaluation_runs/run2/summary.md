# Evaluation analysis

**N/A** means the metric is not applicable or was not computed. A recorded 0 is a measured zero.

- Source: **AWS measurement**
- Run: 2026-10-11T08:05:29+00:00, 9000 requests, 24000 invocations, workers: 1
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
| final deliveries that were cold starts | 6002 |
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
| P1 | 1 | 1 | 1 | 1 | **N/A** | 63.86 | 61.16 | 68.89 | 63.86 | 61.16 | 68.89 | 79.74 | 79.57 | 79.95 | 61.63 | 0.001 | 21.08 |
| P1 | 2 | 2 | 2 | 2 | **N/A** | 2450 | 2447 | 2454 | 5508 | 5504 | 5511 | 2560 | 2550 | 2568 | **N/A** | 1 | 301.6 |
| P1 | 5 | 5 | 5 | 5 | **N/A** | 2452 | 2449 | 2456 | 1.642e+04 | 1.641e+04 | 1.643e+04 | 2553 | 2549 | 2565 | **N/A** | 1 | 299.8 |
| P2 | 1 | 1 | 1 | 1 | 0 | 64.13 | 61.46 | 68.96 | 64.13 | 61.46 | 68.96 | 79.75 | 79.57 | 80.12 | 61.97 | 0.001 | 20.93 |
| P2 | 2 | 2 | 2 | 2 | 1 | 2478 | 2474 | 2482 | 5535 | 5531 | 5539 | 2582 | 2573 | 2590 | **N/A** | 1 | 303.9 |
| P2 | 5 | 5 | 5 | 5 | 4 | 2474 | 2470 | 2478 | 1.644e+04 | 1.643e+04 | 1.645e+04 | 2582 | 2570 | 2591 | **N/A** | 1 | 302 |
| P3 | 1 | 3 | 3 | 3 | 0 | 136.9 | 136 | 137.9 | 136.9 | 136 | 137.9 | 159.8 | 159.6 | 160.1 | 136.9 | 0 | 94.04 |
| P3 | 2 | 4 | 4 | 4 | 1 | 2484 | 2480 | 2488 | 5541 | 5537 | 5545 | 2590 | 2579 | 2601 | **N/A** | 1 | 306 |
| P3 | 5 | 7 | 7 | 7 | 4 | 2481 | 2477 | 2485 | 1.645e+04 | 1.644e+04 | 1.646e+04 | 2588 | 2581 | 2591 | **N/A** | 1 | 305.1 |

### Latency tests (9 tests, Holm-Bonferroni within this family)

| multiplicity | comparison | test | estimate | diff | ci_lo | ci_hi | effect_name | effect | p | p_holm | reject_h0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -0.007 | -0.128 | 0.111 | rank_biserial | -0.003008 | 0.9073 | 0.9073 | False |
| 1 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -79.48 | -79.65 | -79.28 | rank_biserial | -0.9975 | 0 | 0 | True |
| 1 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -79.48 | -79.65 | -79.28 | rank_biserial | -0.9958 | 0 | 0 | True |
| 2 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -28.22 | -34.18 | -20.74 | rank_biserial | -0.2579 | 1.761e-23 | 1.057e-22 | True |
| 2 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -35.39 | -39.89 | -28.74 | rank_biserial | -0.3054 | 2.863e-32 | 2.004e-31 | True |
| 2 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -3.911 | -11.16 | -0.032 | rank_biserial | -0.05188 | 0.04456 | 0.08912 | False |
| 5 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -20.36 | -27.53 | -18.64 | rank_biserial | -0.1958 | 3.38e-14 | 1.352e-13 | True |
| 5 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -28.53 | -33.77 | -20.85 | rank_biserial | -0.2578 | 1.856e-23 | 1.057e-22 | True |
| 5 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -7.332 | -11.96 | -0.355 | rank_biserial | -0.06373 | 0.0136 | 0.04081 | True |

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
