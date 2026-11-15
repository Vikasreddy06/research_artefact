# Lambda idempotency evaluation

This artefact measures how often a retried AWS Lambda function writes the same DynamoDB item again, for three write paths:

- **P1, plain write:** a PutItem of the business item.
- **P2, conditional write:** a PutItem that succeeds only if the item does not exist yet.
- **P3, idempotency-key write:** a tracking item is claimed first, then the business item is written, then the tracking item is marked completed.

A test driver on an EC2 machine sends each synthetic payment request one, two or five times. Every delivery except the last times out just after the write path has finished, so each retry arrives for a write that is already saved. In the sensitivity runs, the timeout falls after P3's business-item write and before the write that marks its tracking item completed. Repeated writes are counted from the table's DynamoDB stream. Each run's `stream.jsonl` holds every table change in the stream's 24-hour window. The analysis keeps only the changes made by the run's own deliveries.

There are two ways to use this artefact:

- **Path A** rebuilds every result table and figure of the thesis from the stored raw data. It needs no AWS account and is the way to check the thesis's numbers.
- **Path B** repeats the experiment on AWS. It needs an AWS account and costs money.

## Folders

| Folder | Contents |
|---|---|
| `src/lambda_fn` | the Lambda function and the three write paths |
| `src/driver` | the test driver: schedule, deliveries, stream download |
| `infra` | Terraform for the table, the stream, the function and its settings |
| `config` | experiment settings, pinned versions and region, list prices for the cost estimate |
| `data/workload` | the card-payment amounts the requests draw from (OpenML dataset 1597), rebuilt by `scripts/fetch_amounts.py` |
| `data/runs/aws` | the raw data of every run, one folder per run (see "Raw data" below); `aws_evidence.json` holds settings read from AWS |
| `analysis`, `scripts` | analysis of the raw data, and helper scripts |
| `results` | tables built from the raw data (guide: `results/README.md`) |
| `figures/aws/thesis_figures` | the result figures of the thesis |
| `notebooks` | `evaluation.ipynb`, which builds the thesis tables and figures |
| `tests` | tests of the code, mostly on an in-memory copy of DynamoDB (moto); these are not measurements |

`results` is laid out in the order of the thesis:

| Folder | Contents |
|---|---|
| `results/report_tables` | start here: the tables behind every number in the thesis's Evaluation and the request amounts in its Methodology |
| `results/pilot` | the pilot sizing |
| `results/evaluation_runs/run1` to `run3` | one analysis per evaluation run; `all_runs` sets the three side by side |
| `results/sensitivity_runs/run1` to `run3` | the sensitivity runs (P3, timeout after its business-item write); `all_runs` sets the three side by side |
| `results/load_runs/100_in_flight`, `900_in_flight` | the load runs with 100 and 900 requests in flight, each with `run1` to `run3` and `all_runs` |

Each run is analysed on its own. The combined tables show each run, or the mean, smallest and largest value of the three.

### What each summary file holds

| File | Contents |
|---|---|
| `results/report_tables/workload.csv` | payment amounts of the source dataset and of each run's requests |
| `results/report_tables/integrity.csv` | integrity check of every run and its CloudWatch comparison |
| `results/report_tables/duplicates.csv` | retries that wrote the business item again, per timeout position, write path, number of deliveries and run, with intervals |
| `results/report_tables/expectations.csv` | the expectations stated before the runs and whether each held |
| `results/report_tables/cost.csv` | write capacity units per request and final-delivery latency per write path and number of deliveries |
| `results/report_tables/latency_tests.csv` | latency tests between write paths, with Hodges-Lehmann shifts and Holm-adjusted p-values |
| `results/report_tables/sensitivity_claims.csv` | claims of an in-progress key and changes to completed keys in the sensitivity runs |
| `results/report_tables/load.csv` | duplicates, latency and cold starts with 100 and 900 requests in flight |
| `results/report_tables/latency_p95.csv` | 95th-percentile final-delivery latency and cold-start share with 1, 100 and 900 requests in flight |
| `figures/aws/thesis_figures/capacity.png` | write capacity units per request |
| `figures/aws/thesis_figures/latency.png` | mean final-delivery latency with 1, 100 and 900 requests in flight |
| `figures/aws/thesis_figures/latency_hist.png` | distribution of final-delivery latency (one delivery, one in flight; five deliveries, 900 in flight) |
| `figures/aws/thesis_figures/load.png` | mean final-delivery latency with 100 and 900 requests in flight (the same data as two panels of `latency.png`) |
| `results/pilot/pilot_report.md` | the evaluation size checked by the pilot |
| `data/runs/aws/<phase>/<run>/deliveries.jsonl`, `stream.jsonl` | every delivery of a run and every change to the table, for following one request through all its deliveries |

## Path A: rebuild every result and figure from the stored data

Needs Python 3.12, `make` and internet access for the first step (it installs the pinned packages). No AWS account is needed. Tested on macOS; Linux works the same way.

**A1. Unpack and enter the folder.**

```
unzip artefact.zip
cd artefact
```

**A2. Create the Python environment.** This makes `.venv` with the packages pinned in `requirements.txt`.

```
make setup
```

**A3. Run the tests.** Expected: `64 passed`.

```
make test
```

**A4. (Optional) Keep the shipped results to compare with afterwards.**

```
cp -r results results_shipped
cp -r figures figures_shipped
```

**A5. Rebuild everything with one command.**

```
make results
```

This runs, in order: the integrity check of every run, the pilot sizing, the analysis of the evaluation and sensitivity runs, the analysis of the load runs, and the notebook, which writes the thesis tables and figures. It prints each step's output, about 200 lines. Three load runs are flagged by the integrity check, as expected (see "Integrity of the runs" below), and the build carries on. Among the output are these three lines:

```
integrity check flagged data/runs/aws/load/w100/run1
integrity check flagged data/runs/aws/load/w100/run3
integrity check flagged data/runs/aws/load/w900/run1
```

**A6. (Optional) Compare with the shipped results.** Both commands print nothing when the rebuilt files are identical to the shipped ones.

```
diff -r -x README.md results_shipped results
diff -r figures_shipped figures
```

The last line of `make results` is a notebook-kernel warning, `[IPKernelApp] WARNING | Kernel is running over TCP without encryption`. It is harmless: the kernel runs on this machine only.

The single steps behind `make results` can also be run on their own:

| Command | What it does |
|---|---|
| `make verify` | integrity check of the pilot, evaluation and sensitivity runs |
| `make pilot-size` | evaluation size needed from the pilot, into `results/pilot` |
| `make analyse` | each evaluation run with its sensitivity run, into `results/evaluation_runs` and `results/sensitivity_runs` |
| `make aggregate-runs` | the three evaluation runs, and the three sensitivity runs, side by side |
| `make analyse-load` | each load run, and the three runs of each level side by side, into `results/load_runs` |
| `make notebook` | runs every cell of `notebooks/evaluation.ipynb` and saves the outputs into it; writes `results/report_tables` and `figures/aws/thesis_figures` |

The notebook can also be opened in Jupyter or VS Code with the `.venv` environment and run with *Run All*. `make functional` runs the driver and the analysis end to end on an in-memory DynamoDB with small sizes, into `data/runs/moto` and `results/moto`; it is a check that the steps fit together, not a measurement, and `make clean` removes it.

## Path B: repeat the experiment on AWS

Needs an AWS account, the AWS CLI version 2, Terraform 1.6 or later and internet access (Terraform installs the pinned boto3 into the function package). The runs cost money: `make budget` prints an estimate of the pilot, evaluation and sensitivity runs from the list prices in `config/prices.yaml`.

**B1. Choose the region.** The region is set once, in `config/versions.yaml` (`region:`). Terraform, the driver and all scripts read it from there. The stored runs used `eu-west-1`. In another region, `config/prices.yaml` still holds eu-west-1 prices, so `make budget` is only a rough estimate.

**B2. Prepare your own machine.** Steps B2, B5 and B9 run on your own machine, with Terraform installed, after `make setup`, and with AWS credentials that can create IAM roles, Lambda functions, DynamoDB tables and CloudWatch log groups, for example an AWS CLI profile: `export AWS_PROFILE=<profile>`. `make deploy` and every run target check the credentials first.

**B3. Create the driver machine.** The driver runs on an EC2 machine in the same region, so the measured latency does not include home-network time. Run these commands on your own machine with the AWS CLI, in the folder that holds `artefact.zip`. If the artefact was cloned from GitHub, make the zip first in that folder: `zip -r artefact.zip artefact -x "artefact/.git/*"`. The commands use the account's default VPC and its default subnet, which gives the machine a public DNS name. In them, `<region>` is the region of B1, `<account>` your 12-digit account number and `<your IP>` your public IP address.

Save this policy as `driver-policy.json`:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": "lambda:InvokeFunction",
     "Resource": "arn:aws:lambda:<region>:<account>:function:idem-eval-fn"},
    {"Effect": "Allow",
     "Action": ["dynamodb:Scan", "dynamodb:BatchWriteItem", "dynamodb:GetItem", "dynamodb:DescribeTable"],
     "Resource": "arn:aws:dynamodb:<region>:<account>:table/idem-eval"},
    {"Effect": "Allow",
     "Action": ["dynamodb:DescribeStream", "dynamodb:GetShardIterator", "dynamodb:GetRecords"],
     "Resource": "arn:aws:dynamodb:<region>:<account>:table/idem-eval/stream/*"},
    {"Effect": "Allow", "Action": ["cloudwatch:GetMetricStatistics", "sts:GetCallerIdentity"],
     "Resource": "*"}
  ]
}
```

Create the role and its instance profile, a security group that allows SSH from your address only, a key pair, and the machine (Amazon Linux 2023, x86_64, 20 GB gp3 disk, t3.micro):

```
export AWS_REGION=<region>
aws iam create-role --role-name idem-eval-driver --assume-role-policy-document \
  '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
    "Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam put-role-policy --role-name idem-eval-driver --policy-name driver \
  --policy-document file://driver-policy.json
aws iam attach-role-policy --role-name idem-eval-driver \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam create-instance-profile --instance-profile-name idem-eval-driver
aws iam add-role-to-instance-profile --instance-profile-name idem-eval-driver \
  --role-name idem-eval-driver

aws ec2 create-security-group --group-name idem-eval-driver \
  --description "idem-eval driver"
aws ec2 authorize-security-group-ingress --group-name idem-eval-driver \
  --protocol tcp --port 22 --cidr <your IP>/32
aws ec2 create-key-pair --key-name idem-eval-driver \
  --query KeyMaterial --output text > idem-eval-driver.pem
chmod 400 idem-eval-driver.pem

AMI=$(aws ssm get-parameter --query Parameter.Value --output text --name \
  /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64)
aws ec2 run-instances --image-id $AMI --instance-type t3.micro \
  --security-groups idem-eval-driver --key-name idem-eval-driver \
  --iam-instance-profile Name=idem-eval-driver \
  --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=20,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=idem-eval-driver}]'

# the instance id and public DNS name (the DNS name changes after every start)
aws ec2 describe-instances --filters Name=tag:Name,Values=idem-eval-driver \
  --query "Reservations[].Instances[].[InstanceId,PublicDnsName]" --output text
```

Copy the artefact to the machine, connect, install Python 3.12 and the tools, and set the artefact up there:

```
scp -i idem-eval-driver.pem artefact.zip ec2-user@<public DNS>:
ssh -i idem-eval-driver.pem ec2-user@<public DNS>
sudo dnf install -y python3.12 python3.12-pip make tmux unzip
unzip -q artefact.zip && cd artefact
make setup && make test
aws sts get-caller-identity      # shows the instance role, so no keys are stored on the machine
```

The driver machine needs no Terraform. Steps B4, B6, B7 and B8 run on it, with its role as credentials. Stop it whenever no run is going (`aws ec2 stop-instances --instance-ids <instance id>`) and start it again with `aws ec2 start-instances --instance-ids <instance id>`.

**B4. Move the stored raw data aside.** The driver never writes into an existing run folder.

```
mv data/runs/aws ../stored_runs_aws
```

**B5. Create the AWS resources.** Terraform creates the table, its stream, the function, its log group, its asynchronous retry setting (0) and its permissions.

```
make deploy
```

**B6. Run the experiment on the driver machine,** inside `tmux`, so the runs continue if the SSH connection drops. Give each run a note that names the driver:

```
make pilot pilot-size NOTE="driver: EC2 <instance type>, <region>"
make evaluation-runs NOTE="driver: EC2 <instance type>, <region>"
make sensitivity-runs NOTE="driver: EC2 <instance type>, <region>"
make load-runs LOAD_LEVELS=100 NOTE="driver: EC2 t3.micro, <region>"
```

The stored runs with 900 in flight used a larger driver, an m7i-flex.large. To do the same, change the machine's type from your own machine, start it again, look up its new public DNS name, connect, and run the 900 level inside `tmux`. Change the type back to t3.micro afterwards in the same way:

```
aws ec2 stop-instances --instance-ids <instance id>
aws ec2 wait instance-stopped --instance-ids <instance id>
aws ec2 modify-instance-attribute --instance-id <instance id> \
  --instance-type Value=m7i-flex.large
aws ec2 start-instances --instance-ids <instance id>
# then, on the driver, inside tmux:
make load-runs LOAD_LEVELS=900 NOTE="driver: EC2 m7i-flex.large, <region>"
```

`make pilot-size` writes the evaluation size into `results/pilot/pilot_choice.json`, and the later targets read it. `make load-runs` sends the evaluation runs' requests again, with the same seeds, with 100 and then 900 requests in flight; `LOAD_LEVELS` selects one level. With one request in flight and the 3 s timeout, one evaluation run takes about 18.4 hours and one sensitivity run about 6.2 hours. The DynamoDB stream keeps records for 24 hours and is read at the end of each run, so a run must finish within that time. The account's Lambda concurrent-executions quota (1,000 by default) limits how many invocations run at once. Each run appends its start time, seed, worker count, note and the exit code of its integrity check to `data/runs/aws/runs.log`.

If the integrity check flags a run, the target stops after that run, and the run's data stay in its folder. Read the run's `verify.json`. If its `problems` list holds only `unplanned_timeouts=1`, with or without `no_mutation=1` (one delivery that timed out before writing), keep the run, as for the three stored load runs. Otherwise move the whole run folder to a folder outside `data/runs/aws`, write down the reason the check gave, and start the run again. Do not delete the moved folder; it is not one of the analysed runs. Then start each remaining run on its own, with the seed and folder given for it in the Makefile, for example:

```
make run PHASE=evaluation N=1000 SEED=127181855 WORKERS=100 OUT=data/runs/aws/load/w100/run2 NOTE="driver: EC2 t3.micro, <region>"
```

**B7. Compare with CloudWatch,** about 15 minutes after the last run. CloudWatch keeps one-minute data for 15 days.

```
make cloudwatch
```

**B8. Build the results and figures** from the new runs on the driver, as in Path A. Then copy the runs and results back to your own machine, after moving the stored ones aside there too:

```
make results
# on your own machine, in the artefact folder:
mv data/runs/aws ../stored_runs_aws_local; mv results ../stored_results_local; mv figures/aws ../stored_figures_local
scp -r -i ../idem-eval-driver.pem ec2-user@<public DNS>:artefact/data/runs/aws data/runs/
scp -r -i ../idem-eval-driver.pem ec2-user@<public DNS>:artefact/results .
scp -r -i ../idem-eval-driver.pem ec2-user@<public DNS>:artefact/figures/aws figures/
```

**B9. Delete the AWS resources** from your own machine, then terminate the driver machine and remove its role, security group and key pair:

```
make destroy
aws ec2 terminate-instances --instance-ids <instance id>
aws ec2 wait instance-terminated --instance-ids <instance id>
aws ec2 delete-security-group --group-name idem-eval-driver
aws ec2 delete-key-pair --key-name idem-eval-driver
aws iam remove-role-from-instance-profile --instance-profile-name idem-eval-driver \
  --role-name idem-eval-driver
aws iam delete-instance-profile --instance-profile-name idem-eval-driver
aws iam detach-role-policy --role-name idem-eval-driver \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam delete-role-policy --role-name idem-eval-driver --policy-name driver
aws iam delete-role --role-name idem-eval-driver
```

## Raw data

Every run folder in `data/runs/aws` holds the records written while the run happened on AWS:

| File | Contents |
|---|---|
| `schedule.csv`, `ground_truth.jsonl` | the requests and the number of deliveries of each, fixed before the run |
| `deliveries.jsonl` | the driver's record of every delivery: outcome, write capacity units, latency, cold start |
| `stream.jsonl` | every table change from the DynamoDB stream, the ground truth for repeated writes |
| `run_info.json` | settings, seed, start and end time of the run |
| `verify.json` | the result of the integrity check |
| `cloudwatch.json` | the CloudWatch comparison (evaluation and sensitivity runs) |

## Runs

| Run folder | Kind | Requests per cell | Seed | Duration |
|---|---|---|---|---|
| `pilot` | pilot | 50 per write path | 25178849 | 14 min |
| `evaluation/run1` | evaluation, 1 in flight | 1,000 | 125181849 | 18 h 18 min |
| `evaluation/run2` | evaluation, 1 in flight | 1,000 | 127181855 | 18 h 23 min |
| `evaluation/run3` | evaluation, 1 in flight | 1,000 | 128181858 | 18 h 25 min |
| `sensitivity/run1` | sensitivity (P3 only) | 1,000 | 26178849 | 6 h 8 min |
| `sensitivity/run2` | sensitivity (P3 only) | 1,000 | 27178849 | 6 h 14 min |
| `sensitivity/run3` | sensitivity (P3 only) | 1,000 | 28178849 | 6 h 11 min |
| `load/w100/run1` | load, 100 in flight | 1,000 | 125181849 | 11 min |
| `load/w100/run2` | load, 100 in flight | 1,000 | 127181855 | 11 min |
| `load/w100/run3` | load, 100 in flight | 1,000 | 128181858 | 11 min |
| `load/w900/run1` | load, 900 in flight | 1,000 | 125181849 | 1.4 min |
| `load/w900/run2` | load, 900 in flight | 1,000 | 127181855 | 1.4 min |
| `load/w900/run3` | load, 900 in flight | 1,000 | 128181858 | 1.4 min |

Settings of every run:

- **Function:** Python 3.12, 128 MB, 3 s timeout, x86_64; Lambda's own asynchronous retries set to 0. All runs used the same function code and settings: the function's `LastModified` time in `aws_evidence.json` (10 October 2026, 13:26 UTC) is before the start of the pilot (13:31 UTC).
- **Table:** on-demand capacity, stream with the item before and after each change.
- **Region:** eu-west-1.
- **Driver:** Amazon Linux 2023, Python 3.12, in eu-west-1c. A t3.micro for all runs except the load runs with 900 in flight, which used an m7i-flex.large. The account's Lambda concurrent-executions quota is 1,000 (read on 14 November 2026, `aws_evidence.json`).

`data/runs/aws/aws_evidence.json` holds settings read from AWS on 14 November 2026 with read-only AWS CLI calls (Lambda, EC2, Service Quotas and the CloudTrail event history, which keeps 90 days): the function's configuration, the account's concurrency quota, the driver's machine image and, from AWS CloudTrail, the times the driver's instance type was changed for the runs with 900 in flight.

### Integrity of the runs

The pilot, evaluation and sensitivity runs passed every integrity check. In three load runs, one delivery timed out before it wrote: `load/w100/run1` and `load/w100/run3` (the last delivery of a P1 request with five deliveries) and `load/w900/run1` (the only delivery of a P2 request, which was never written). The integrity check flags these three runs. They are analysed with that delivery counted as it happened.

## Known limits

- DynamoDB does not report the write units of a failed conditional write. The function adds them by the documented rule (`wcu_ccf_rule`: the item size in KB, rounded up, at least one unit). P3 sizes the existing tracking item that DynamoDB returns. P2 sizes the business item it tried to write, which is padded to the same size as the stored one. Both give one unit. These units are not measured one by one, and every capacity figure includes them. The total of reported and rule units agrees with CloudWatch's `ConsumedWriteCapacityUnits` within three units in each evaluation and sensitivity run (`cloudwatch.json`).
- The CloudWatch check covers the evaluation and sensitivity runs. It compares only the whole minutes inside each run, so a few writes at the minute boundaries are left out.
- The retries are sent by the test driver as synchronous invocations. The timeout falls after the write path has finished or, for P3, after its business-item write and before its completed mark, so only these two timeout positions are tested. The deliveries of one request never overlap.
- With one request in flight, every final delivery at two and five deliveries was a cold start, so its latency is mostly cold-start time. In the load runs, some retries reached an already running copy of the function and some first deliveries a new one, so the cold-start share and the latency differ by load level. The driver's round trip includes the network time inside the region.

## Folders created when the commands run

`.venv` is created by `make setup`. `infra/.terraform` is created by `make tf-check` or `make deploy`, and `infra/terraform.tfstate` and `build` by `make deploy`. `data/runs/moto` and `results/moto` are created by `make functional`.
