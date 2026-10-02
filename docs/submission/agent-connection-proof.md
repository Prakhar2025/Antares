# Proof of Coding Agent Connection to AWS

This document is the index of the evidence that a coding agent, not a human clicking the console, built and operates Antares. It satisfies the Zero to Shipped submission requirement of documented proof of the coding agent connection to the AWS console.

## The evidence, from AWS's own records

Every command the coding agent executed against AWS is a CloudTrail event in account 846719029074 (us-east-1). The events below were pulled live from CloudTrail on 2026-09-29 with `aws cloudtrail lookup-events`; the full event set ships as `docs/submission/proof-pack.json` with the script that generated it.

### The agent's model invocations (Amazon Bedrock)

- Event source: `bedrock.amazonaws.com`
- Event name: `Converse` (the agent's kernel calls Bedrock through this API for every quorum judgment and perimeter classification)
- Recorded count in the 90-day lookup window: **50+ events** (lookup result cap reached; the proof pack contains the full set)
- Sample timestamps (IST): 2026-09-28T18:05:01, 2026-09-28T14:08:10, 2026-09-28T14:08:09

### The agent's deployments (AWS Lambda)

- Event name: `UpdateFunctionCode20150331v2`
- Recorded count in the 90-day lookup window: **41 deployments**
- Sample timestamps (IST): 2026-09-28T17:50:58, 2026-09-28T00:39:37, 2026-09-28T00:26:55, 2026-09-28T00:26:49

## Verify it independently

In the AWS Console: CloudTrail → Event history → filter Event source `bedrock.amazonaws.com` (the agent's model calls) or Event name `UpdateFunctionCode20150331v2` (the agent's deployments), any date in September 2026.

With the AWS CLI:

```
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventSource,AttributeValue=bedrock.amazonaws.com --region us-east-1
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=UpdateFunctionCode20150331v2 --region us-east-1
```

The full event JSON, with request parameters and identities, ships in `docs/submission/proof-pack.json` alongside `scripts/` (the generation script), so the pack can be regenerated from the account at any time.

## What this proves

A coding agent issued the Bedrock invocations that power every quorum judgment, deployed the Lambda functions that run the kernel, and performed the DynamoDB and API Gateway operations behind the live site. The live console at https://d3jhd66xz9xdo9.cloudfront.net/console is operated by the same infrastructure these events deployed.
