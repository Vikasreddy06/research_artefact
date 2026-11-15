# The Terraform files match config/
from pathlib import Path

import hcl2
import yaml

INFRA = Path("infra")
V = yaml.safe_load(open("config/versions.yaml"))
E = yaml.safe_load(open("config/experiment.yaml"))


def unq(v):
    if isinstance(v, list):
        return [unq(x) for x in v]
    return v.strip('"') if isinstance(v, str) else v


def load(name):
    with open(INFRA / name) as fh:
        return hcl2.load(fh)


def resources():
    out = {}
    for block in load("main.tf").get("resource", []):
        for rtype, named in block.items():
            for name, body in named.items():
                out[(unq(rtype), unq(name))] = body
    return out


def test_function_runtime_architecture_and_handler():
    fn = resources()[("aws_lambda_function", "fn")]
    assert unq(fn["runtime"]) == V["lambda"]["runtime"]
    assert unq(fn["architectures"]) == [V["lambda"]["architecture"]]
    assert unq(fn["handler"]) == "lambda_fn.handler.lambda_handler"


def test_table_is_on_demand_with_streams_and_destroyable():
    t = resources()[("aws_dynamodb_table", "items")]
    assert unq(t["billing_mode"]) == "PAY_PER_REQUEST"
    assert t["stream_enabled"] is True and unq(t["stream_view_type"]) == V["dynamodb"]["streams"]
    assert t["deletion_protection_enabled"] is False


def test_platform_retries_are_off():
    assert resources()[("aws_lambda_function_event_invoke_config", "no_retries")]["maximum_retry_attempts"] == 0
