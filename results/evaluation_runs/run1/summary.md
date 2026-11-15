# Evaluation analysis

**N/A** means the metric is not applicable or was not computed. A recorded 0 is a measured zero.

- Source: **AWS measurement**
- Run: 2026-10-10T13:46:54+00:00, 9000 requests, 24000 invocations, workers: 1
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
| P1 | 1 | 1 | 1 | 1 | **N/A** | 61.82 | 61.15 | 62.49 | 61.82 | 61.15 | 62.49 | 79.81 | 79.57 | 80.02 | 61.82 | 0 | 20.88 |
| P1 | 2 | 2 | 2 | 2 | **N/A** | 2434 | 2428 | 2440 | 5491 | 5485 | 5496 | 2561 | 2544 | 2567 | **N/A** | 1 | 298.9 |
| P1 | 5 | 5 | 5 | 5 | **N/A** | 2428 | 2422 | 2433 | 1.635e+04 | 1.634e+04 | 1.636e+04 | 2543 | 2541 | 2561 | **N/A** | 1 | 297.2 |
| P2 | 1 | 1 | 1 | 1 | 0 | 61.7 | 61.01 | 62.45 | 61.7 | 61.01 | 62.45 | 80.04 | 79.74 | 80.62 | 61.7 | 0 | 20.75 |
| P2 | 2 | 2 | 2 | 2 | 1 | 2457 | 2452 | 2462 | 5513 | 5507 | 5518 | 2579 | 2562 | 2583 | **N/A** | 1 | 301.1 |
| P2 | 5 | 5 | 5 | 5 | 4 | 2456 | 2451 | 2462 | 1.638e+04 | 1.637e+04 | 1.639e+04 | 2590 | 2580 | 2602 | **N/A** | 1 | 300.1 |
| P3 | 1 | 3 | 3 | 3 | 0 | 136.9 | 134.1 | 141.5 | 136.9 | 134.1 | 141.5 | 160 | 159.8 | 160.4 | 134.9 | 0.001 | 92.79 |
| P3 | 2 | 4 | 4 | 4 | 1 | 2457 | 2451 | 2463 | 5513 | 5508 | 5519 | 2581 | 2571 | 2588 | **N/A** | 1 | 302.2 |
| P3 | 5 | 7 | 7 | 7 | 4 | 2457 | 2451 | 2463 | 1.638e+04 | 1.636e+04 | 1.639e+04 | 2581 | 2568 | 2584 | **N/A** | 1 | 302 |

### Latency tests (9 tests, Holm-Bonferroni within this family)

| multiplicity | comparison | test | estimate | diff | ci_lo | ci_hi | effect_name | effect | p | p_holm | reject_h0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | 0.059 | -0.056 | 0.176 | rank_biserial | 0.02649 | 0.3051 | 0.9038 | False |
| 1 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -79.06 | -79.3 | -78.72 | rank_biserial | -0.9979 | 0 | 0 | True |
| 1 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -79.1 | -79.34 | -78.77 | rank_biserial | -0.996 | 0 | 0 | True |
| 2 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -21.17 | -30.24 | -18.92 | rank_biserial | -0.1737 | 1.745e-11 | 6.979e-11 | True |
| 2 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -23.03 | -31.7 | -19.53 | rank_biserial | -0.1818 | 1.936e-12 | 9.678e-12 | True |
| 2 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -0.5105 | -8.598 | 3.387 | rank_biserial | -0.01383 | 0.5922 | 0.9038 | False |
| 5 | P1 vs P2 | mann_whitney_u | Hodges-Lehmann shift | -28.22 | -34.81 | -20.38 | rank_biserial | -0.2062 | 1.42e-15 | 8.52e-15 | True |
| 5 | P1 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -31.29 | -39.53 | -23.41 | rank_biserial | -0.2311 | 3.57e-19 | 2.499e-18 | True |
| 5 | P2 vs P3 | mann_whitney_u | Hodges-Lehmann shift | -1.603 | -10.48 | 1.533 | rank_biserial | -0.0267 | 0.3013 | 0.9038 | False |

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
