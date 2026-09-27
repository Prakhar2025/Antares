"""Kill-switch drill: halt the gate, verify 503, revert, verify gate returns."""

import json
import subprocess
import sys
import time

import boto3
import urllib.request

lambda_client = boto3.client("lambda", region_name="us-east-1")
ssm = boto3.client("ssm", region_name="us-east-1")
stack = boto3.client("cloudformation", region_name="us-east-1")

outputs = stack.describe_stacks(StackName="antares-dev")["Stacks"][0]["Outputs"]
api_url = next(o["OutputValue"] for o in outputs if o["OutputKey"] == "ApiUrl")

base_vars = {
    "ANTARES_TABLE_NAME": "antares-dev-main",
    "ANTARES_POLICY_VERSION": "1.0",
    "ANTARES_ALLOWED_TABLES": "antares-dev-main,antares-dev-ledger",
    "ANTARES_ALLOWED_BUCKETS": "antares-dev-vault",
    "ANTARES_SSM_PREFIX": "/antares/dev/",
    "ANTARES_REASONER_MODEL": "us.amazon.nova-pro-v1:0",
    "ANTARES_ADVERSARY_MODEL": "us.meta.llama3-3-70b-instruct-v1:0",
    "ANTARES_PERIMETER_MODEL": "us.amazon.nova-lite-v1:0",
    "ANTARES_SIGNING_KEY_ID": "alias/antares-dev-signing",
    "POWERTOOLS_SERVICE_NAME": "antares-gate",
    "POWERTOOLS_METRICS_NAMESPACE": "Antares",
    "LOG_LEVEL": "INFO",
}


def set_env(halt: bool) -> None:
    variables = {**base_vars, "ANTARES_HALT": "true" if halt else "false"}
    lambda_client.update_function_configuration(
        FunctionName="antares-dev-gate",
        Environment={"Variables": variables},
    )
    time.sleep(8)


def gate() -> tuple[int, str]:
    body = json.dumps({
        "call_id": f"drill-{int(time.time())}",
        "tool": "ledger.describe",
        "action": "dynamodb:DescribeTable",
        "params": {"table": "antares-dev-ledger"},
        "session": {"session_id": "session-drill"},
        "requested_by": "agent/drill",
    }).encode()
    request = urllib.request.Request(
        f"{api_url}/v1/gate", data=body, headers={"Content-Type": "application/json"}
    )
    try:
        response = urllib.request.urlopen(request, timeout=30)
        return response.status, response.read().decode()[:120]
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()[:120]


print("=== halt ===")
set_env(True)
time.sleep(3)
status, body = gate()
print("halted gate:", status, body[:100])
assert status == 503, "kill switch did not produce 503"

print("=== revert ===")
set_env(False)
time.sleep(3)
status, body = gate()
print("restored gate:", status)
assert status == 200, "gate did not recover"

print("DRILL PASSED: halt produced 503, revert restored service")
