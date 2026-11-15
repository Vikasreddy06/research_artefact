# Evaluation analysis

**N/A** means the metric is not applicable or was not computed. A recorded 0 is a measured zero.

- Source: **AWS measurement**
- Run: 2026-10-22T15:47:20+00:00, 9000 requests, 24000 invocations, workers: 100
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
| final deliveries that were cold starts | 5857 |
| mutation ground truth | stream |

## Duplicate mutation per injected retry (95 % Wilson and cluster-bootstrap CIs)

| path | multiplicity | requests | injected_retries | dup_mutations | dup_rate | dup_ci_lo | dup_ci_hi | dup_cluster_ci_lo | dup_cluster_ci_hi | dup_request_share | dup_request_ci_lo | dup_request_ci_hi | ccf_per_retry | successful_retry_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 1 | 1000 | 0 | 0 | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** | **N/A** |
| P1 | 2 | 1000 | 1000 | 1000 | 1 | 0.9962 | 1 | 1 | 1 | 1 | 0.9962 | 1 | **N/A** | 0 |
| P1 | 5 | 1000 | 4000 | 3999 | 0.9998 | 0.9986 | 1 | 0.9992 | 1 | 1 | 0.9962 | 1 | **N/A** | 0.00025 |
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
| P1 | 1 | 1 | 1 | 1 | **N/A** | 615.8 | 557.8 | 680.7 | 615.8 | 557.8 | 680.7 | 2483 | 2468 | 2505 | 61.52 | 0.233 | 84.81 |
| P1 | 2 | 2 | 2 | 2 | **N/A** | 2108 | 2057 | 2157 | 5302 | 5249 | 5355 | 2542 | 2536 | 2549 | 60.76 | 0.862 | 261.1 |
| P1 | 5 | 4.999 | 4.997 | 5 | **N/A** | 2131 | 2080 | 2178 | 1.599e+04 | 1.594e+04 | 1.605e+04 | 2543 | 2527 | 2551 | 59.69 | 0.871 | 262.9 |
| P2 | 1 | 1 | 1 | 1 | 0 | 530.6 | 471.5 | 588.3 | 530.6 | 471.5 | 588.3 | 2465 | 2456 | 2481 | 59.9 | 0.198 | 75.1 |
| P2 | 2 | 2 | 2 | 2 | 1 | 2130 | 2077 | 2178 | 5331 | 5276 | 5382 | 2572 | 2560 | 2582 | 68.67 | 0.861 | 262.7 |
| P2 | 5 | 5 | 5 | 5 | 4 | 2165 | 2117 | 2209 | 1.603e+04 | 1.597e+04 | 1.608e+04 | 2570 | 2562 | 2582 | 70.71 | 0.877 | 267.3 |
| P3 | 1 | 3 | 3 | 3 | 0 | 648.3 | 586.6 | 704.3 | 648.3 | 586.6 | 704.3 | 2552 | 2536 | 2573 | 133.6 | 0.216 | 153.5 |
| P3 | 2 | 4 | 4 | 4 | 1 | 2139 | 2088 | 2191 | 5330 | 5277 | 5384 | 2565 | 2558 | 2581 | 72.97 | 0.864 | 265.2 |
| P3 | 5 | 7 | 7 | 7 | 4 | 2166 | 2118 | 2212 | 1.604e+04 | 1.598e+04 | 1.609e+04 | 2568 | 2562 | 2581 | 75.81 | 0.875 | 267.9 |

### Latency tests (9 tests, Holm-Bonferroni within this family)

| multiplicity | comparison | test | estimate | diff | ci_lo | ci_hi | effect_name | effect | p | p_holm | reject_h0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | 0.345 | 0.07 | 0.67 | rank_biserial | 0.06312 | 0.01452 | 0.04357 | True |
| 1 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -76.83 | -78.27 | -73.82 | rank_biserial | -0.605 | 2.293e-121 | 1.834e-120 | True |
| 1 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -78.53 | -79.19 | -77.42 | rank_biserial | -0.6694 | 3.947e-148 | 3.552e-147 | True |
| 2 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -24.53 | -31.73 | -19.47 | rank_biserial | -0.2036 | 3.231e-15 | 1.616e-14 | True |
| 2 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -26.56 | -33.22 | -20.36 | rank_biserial | -0.217 | 4.332e-17 | 2.599e-16 | True |
| 2 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -0.823 | -7.415 | 4.049 | rank_biserial | -0.01335 | 0.6054 | 0.6054 | False |
| 5 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -23.02 | -30.1 | -18.88 | rank_biserial | -0.1991 | 1.274e-14 | 5.097e-14 | True |
| 5 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -29.8 | -36.92 | -22.78 | rank_biserial | -0.2431 | 4.748e-21 | 3.324e-20 | True |
| 5 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -5.622 | -12.09 | 0.152 | rank_biserial | -0.04823 | 0.06184 | 0.1237 | False |

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
