# Experiment runs on AWS and analysis of the stored data
PY ?= .venv/bin/python
WORKERS ?= 1
export PYTHONPATH := src:.

AWS_RUNS := data/runs/aws
MOTO := data/runs/moto
ALL_RUNS := results/evaluation_runs/all_runs
SENS_ALL := results/sensitivity_runs/all_runs
PILOT_OUT := results/pilot
RUNS := $(AWS_RUNS)/evaluation/run1 $(AWS_RUNS)/evaluation/run2 $(AWS_RUNS)/evaluation/run3
SENS_RUNS = $(sort $(wildcard $(AWS_RUNS)/sensitivity/run*))
LOAD_RUNS = $(foreach w,100 900,$(foreach i,1 2 3,$(AWS_RUNS)/load/w$(w)/run$(i)))
# Evaluation size from the pilot check
EVAL_N = $(shell $(PY) -c "import json; print(json.load(open('$(PILOT_OUT)/pilot_choice.json'))['N'])")

.PHONY: setup test lint tf-check budget check-aws-creds deploy run pilot \
	evaluation-runs sensitivity-runs load-runs cloudwatch pilot-size analyse aggregate-runs verify \
	analyse-load results \
	functional notebook destroy clean

# ---- local, no AWS ----
setup:
	python3.12 -m venv .venv
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check src tests scripts analysis

tf-check:
	cd infra && terraform fmt -check -recursive && terraform init -backend=false -input=false && terraform validate

budget:
	$(PY) scripts/budget_estimate.py

# ---- AWS (needs credentials) ----
check-aws-creds:
	@test -x $(PY) || { echo "ERROR: no Python environment here; run make setup first."; exit 1; }
	@$(PY) -c "import boto3, yaml; boto3.client('sts', region_name=yaml.safe_load(open('config/versions.yaml'))['region']).get_caller_identity()" >/dev/null 2>&1 || { \
		echo "ERROR: no working AWS credentials (profile, environment variables or instance role)."; \
		exit 1; }

deploy: check-aws-creds
	cd infra && terraform init -input=false && terraform apply -var python=$(PY)

# One run: clear the table, send the deliveries, save the stream, check the run; logged in runs.log
run: check-aws-creds
	@mkdir -p $(AWS_RUNS)
	@echo "$$(date -u +%FT%TZ) start $(OUT) phase=$(PHASE) n=$(N) seed=$(SEED) workers=$(WORKERS) note=$(NOTE)" >> $(AWS_RUNS)/runs.log
	$(PY) scripts/clear_table.py
	$(PY) -m driver.run --phase $(PHASE) $(if $(N),--n $(N)) --seed $(SEED) --workers $(WORKERS) --out $(OUT)
	$(PY) -m driver.streams --out $(OUT)
	$(PY) scripts/verify_evaluation_run.py --run $(OUT); s=$$?; \
		echo "$$(date -u +%FT%TZ) end $(OUT) verify_exit=$$s" >> $(AWS_RUNS)/runs.log; exit $$s

pilot:
	$(MAKE) run PHASE=pilot SEED=25178849 OUT=$(AWS_RUNS)/pilot

# The three evaluation runs
evaluation-runs:
	$(MAKE) run PHASE=evaluation N=$(EVAL_N) SEED=125181849 OUT=$(AWS_RUNS)/evaluation/run1
	$(MAKE) run PHASE=evaluation N=$(EVAL_N) SEED=127181855 OUT=$(AWS_RUNS)/evaluation/run2
	$(MAKE) run PHASE=evaluation N=$(EVAL_N) SEED=128181858 OUT=$(AWS_RUNS)/evaluation/run3

# The three sensitivity runs (P3 only, timeout after its business-item write, before its completed mark)
sensitivity-runs:
	$(MAKE) run PHASE=sensitivity N=$(EVAL_N) SEED=26178849 OUT=$(AWS_RUNS)/sensitivity/run1
	$(MAKE) run PHASE=sensitivity N=$(EVAL_N) SEED=27178849 OUT=$(AWS_RUNS)/sensitivity/run2
	$(MAKE) run PHASE=sensitivity N=$(EVAL_N) SEED=28178849 OUT=$(AWS_RUNS)/sensitivity/run3

# The six load runs: the evaluation seeds with 100, then 900, requests in flight
# (the stored 900-in-flight runs used an EC2 m7i-flex.large driver, all others a t3.micro)
LOAD_LEVELS ?= 100 900
load-runs:
	for w in $(LOAD_LEVELS); do \
		$(MAKE) run PHASE=evaluation N=$(EVAL_N) SEED=125181849 WORKERS=$$w OUT=$(AWS_RUNS)/load/w$$w/run1 || exit 1; \
		$(MAKE) run PHASE=evaluation N=$(EVAL_N) SEED=127181855 WORKERS=$$w OUT=$(AWS_RUNS)/load/w$$w/run2 || exit 1; \
		$(MAKE) run PHASE=evaluation N=$(EVAL_N) SEED=128181858 WORKERS=$$w OUT=$(AWS_RUNS)/load/w$$w/run3 || exit 1; done

cloudwatch: check-aws-creds
	for d in $(RUNS) $(SENS_RUNS); do $(PY) scripts/collect_cloudwatch.py --run $$d; done

destroy: check-aws-creds
	cd infra && terraform destroy

# ---- analysis of the stored raw data (no AWS) ----
pilot-size:
	$(PY) analysis/pilot_size.py --run $(AWS_RUNS)/pilot --out $(PILOT_OUT) --workers $(WORKERS)

# Analyse each run
analyse:
	for i in 1 2 3; do $(PY) analysis/analyse.py --evaluation $(AWS_RUNS)/evaluation/run$$i \
		--sensitivity $(AWS_RUNS)/sensitivity/run$$i --out results/evaluation_runs/run$$i \
		--sensitivity-out results/sensitivity_runs/run$$i || exit 1; done

aggregate-runs:
	$(PY) analysis/aggregate_runs.py --out $(ALL_RUNS) $(RUNS)
	$(PY) analysis/aggregate_runs.py --out $(SENS_ALL) --name sensitivity_runs $(SENS_RUNS)

verify:
	for d in $(AWS_RUNS)/pilot $(RUNS) $(SENS_RUNS); do $(PY) scripts/verify_evaluation_run.py --run $$d; done

# Analyse each load run and set the three runs of each level side by side
analyse-load:
	for w in 100 900; do for i in 1 2 3; do \
		$(PY) analysis/analyse.py --evaluation $(AWS_RUNS)/load/w$$w/run$$i --out results/load_runs/$${w}_in_flight/run$$i || exit 1; done; \
		$(PY) analysis/aggregate_runs.py --out results/load_runs/$${w}_in_flight/all_runs --name load_w$${w}_runs \
			$(AWS_RUNS)/load/w$$w/run1 $(AWS_RUNS)/load/w$$w/run2 $(AWS_RUNS)/load/w$$w/run3 || exit 1; done

# Every result and figure from the stored raw data, in one command (no AWS). Three load runs are
# flagged by the integrity check (one delivery timed out before writing, see the README); the build goes on.
results:
	$(MAKE) verify
	for d in $(LOAD_RUNS); do $(PY) scripts/verify_evaluation_run.py --run $$d >/dev/null || echo "integrity check flagged $$d"; done
	$(MAKE) pilot-size analyse aggregate-runs analyse-load notebook

# ---- local functional check on moto, not a measurement ----
functional:
	rm -rf $(MOTO)
	$(PY) -m driver.run --backend local --moto --phase pilot --out $(MOTO)/pilot
	$(PY) analysis/pilot_size.py --run $(MOTO)/pilot --out results/moto
	$(PY) -m driver.run --backend local --moto --phase evaluation --n 30 --out $(MOTO)/evaluation
	$(PY) -m driver.run --backend local --moto --phase sensitivity --n 20 --out $(MOTO)/sensitivity
	$(PY) analysis/analyse.py --evaluation $(MOTO)/evaluation --sensitivity $(MOTO)/sensitivity \
		--out results/moto

clean:
	rm -rf build $(MOTO) results/moto

# Run the Evaluation notebook (tables in results/report_tables, figures in figures/aws/thesis_figures)
notebook:
	$(PY) -c "import nbformat; from nbclient import NotebookClient; nb = nbformat.read('notebooks/evaluation.ipynb', 4); NotebookClient(nb, timeout=900, resources={'metadata': {'path': 'notebooks'}}).execute(); nbformat.write(nb, 'notebooks/evaluation.ipynb')"
