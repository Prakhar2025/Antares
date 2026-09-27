"""Debug: ledger conditional head put against real DynamoDB."""

import sys

sys.path.insert(0, "src")

import boto3  # noqa: E402

from antares.ledger import Ledger  # noqa: E402
from antares.saga import canonical_json, sha256_hex  # noqa: E402

ddb = boto3.client("dynamodb", region_name="us-east-1")
ledger = Ledger(ddb, "antares-dev-main")

head = ledger._head()
print("head:", head)
leaf = sha256_hex(canonical_json({"record_type": "debug", "n": 1}))
try:
    ddb.put_item(
        TableName="antares-dev-main",
        Item={
            "pk": {"S": "CHAIN"},
            "sk": {"S": "HEAD"},
            "leaf_hash": {"S": leaf},
            "prev_leaf_hash": {"S": head["leaf_hash"]},
            "height": {"N": str(head["height"] + 1)},
            "ts": "debug",
        },
        ConditionExpression="attribute_not_exists(pk) OR leaf_hash = :expected",
        ExpressionAttributeValues={":expected": {"S": head["leaf_hash"]}},
    )
    print("conditional put ok")
except Exception as error:  # noqa: BLE001
    print(type(error).__name__, str(error)[:400])
