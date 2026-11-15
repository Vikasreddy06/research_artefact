# Results

These tables come from the raw data of the runs in `data/runs/aws/`. The main README explains how to produce them again.

- `results/moto/`: appears only after the local functional check. It is a local check on an in-memory copy of DynamoDB, **not a measurement**. Every other folder holds the runs measured on AWS (the results in the thesis).

## Where to look

| To see | Open |
|---|---|
| The numbers of the thesis Evaluation | `report_tables/` (written by the notebook) |
| The thesis figures | `../figures/aws/thesis_figures/` (the figures of the thesis Evaluation) |
| How the evaluation size was chosen | `pilot/pilot_report.md` |
| A readable summary of one run | `evaluation_runs/run1/summary.md` |
| The three runs side by side | `evaluation_runs/all_runs/`, `sensitivity_runs/all_runs/` |

## Folders

The folders follow the order of the thesis.

```
results/
├── report_tables/     start here: the tables behind the thesis Evaluation
├── pilot/             the pilot sizing
├── evaluation_runs/   run1/ run2/ run3/ and all_runs/ (side by side)
├── sensitivity_runs/  run1/ run2/ run3/ and all_runs/ (P3, timeout after its business-item write)
└── load_runs/         100_in_flight/ and 900_in_flight/, each with run1/ run2/ run3/ and all_runs/
```

Every table is a CSV file. Each evaluation and load run folder also has `summary.md` (the run's results on one readable page, including its sensitivity run for the evaluation runs) and `analysis_info.json` (which raw run was analysed, with the settings). `pilot/` holds `pilot_report.md`, `pilot_sizing.csv` and `pilot_choice.json`.

The three evaluation runs are separate repeats with their own seeds. Each run is analysed on its own. The tables in `report_tables/` show each run, or the mean, smallest and largest value of the three.

## Tables in each run folder

| File | One row per | Holds |
|---|---|---|
| `cells` | write path × number of deliveries | duplicate-mutation rate with its intervals, write capacity, latency, integrity counts |
| `dup_tests` | comparison | z-tests of the duplicate-mutation rate (P1 against P2 and P3; P2 against P3 as exploratory, N/A when both rates are 0), with Holm-corrected p-values |
| `latency_tests` | comparison | latency tests between write paths (Mann-Whitney U, or Welch's t if both samples pass the Shapiro-Wilk test; in these runs none did), Hodges-Lehmann shift, effect size, Holm-corrected p-values |
| `expectations` | expectation | E1 and E2, stated before the runs, and whether each was supported; E3 is reported as a count |
| `chi2` | table | chi-squared tests of the duplicate rate across cells |
| `checks` | check | integrity checks of the run (missing deliveries, errors, deliveries with no function record, cold starts) |
| `sensitivity_cells` | number of deliveries | as `cells`, for the sensitivity run (P3, timeout after its business-item write); in `sensitivity_runs/runN` only |
| `sensitivity_outcomes` | final outcome | how the last delivery of each sensitivity request ended; in `sensitivity_runs/runN` only |
| `requests` | request | every request: its deliveries, capacity, latency and mutations |

## Main columns

- `multiplicity`: the number of deliveries of each request (1, 2 or 5); the injected retries are one fewer.
- `dup_rate`: duplicate mutations divided by injected retries, counted from the DynamoDB stream. `dup_ci_lo`/`hi` is the Wilson interval, `dup_cluster_ci_lo`/`hi` the request-level bootstrap interval, and `dup_request_*` the Wilson interval of the share of requests with any duplicate.
- `capacity_mean`: write capacity units used by all deliveries of a request. It is the sum of `capacity_reported_mean` (reported by DynamoDB) and `capacity_rule_mean` (failed conditional writes, counted by the documented rule because DynamoDB does not report them). The rule units are not measured per write. The driver's total agrees with CloudWatch within three units in each evaluation and sensitivity run (`cloudwatch.json` in each of these run folders under `data/runs/aws/`).
- `re-sent` (in `report_tables/integrity.csv`): invocations the driver sent again after throttling, a Lambda service error or a network error.
- `latency_mean_ms`: round-trip time of the final delivery, timed by the driver on EC2. `cold_final_share` is the share of final deliveries that were cold starts.
- `ccf_per_retry`: share of retries whose conditional write failed.

## Missing values and zeros

- **N/A** means the value does not apply or was not computed. For example, the duplicate rate with one delivery (there is no retry), or P1's conditional-write columns (P1 has no conditional write). In `report_tables/integrity.csv`, the CloudWatch columns are N/A for the load runs, because the CloudWatch check covers only the evaluation and sensitivity runs.
- **0** is a measured zero. For example, P2 and P3 had 0 duplicate mutations, and the integrity counts were 0.
- A p-value shown as 0 is smaller than the computer can represent; report it as p < 0.001.
