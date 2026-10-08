# Architecture and data flow

## Boundary

The Terraform root module targets one AWS account and one home region. It is not an AWS Organizations landing zone. `expected_account_id` must match the caller account before the AWS provider operates. The CloudTrail trail uses the home region for its trail configuration while recording compatible management events across regions.

## Resource inventory

| Component | Role | Network exposure / charging note |
| --- | --- | --- |
| VPC and two private subnets | Demonstrate two-AZ workload placement | No workloads or public route; VPC/subnets alone have no hourly compute charge |
| Two route tables | Explicit isolated routing per subnet | Only AWS's implicit VPC local route |
| S3 audit bucket | Central destination for CloudTrail and VPC Flow Logs | S3 storage and requests can incur charges |
| S3 hardening resources | Public access block, ownership, SSE-S3, versioning, lifecycle, TLS-only policy | Versions and retention affect storage cost |
| CloudTrail | Multi-region read/write management-event recording | Check existing trails and CloudTrail pricing before use |
| VPC Flow Log | All accepted and rejected VPC traffic to S3 | Flow Log delivery and S3 storage can incur charges |
| AWS Budget | Account-wide monthly cost warnings | Alerts are informational, not a spending cap |

## Traffic and logs

No workload or route to the internet is deployed. If a workload is later placed in a private subnet, it can communicate within the VPC CIDR only until a deliberately reviewed route or endpoint is added. VPC Flow Logs observe network metadata, not packet contents. CloudTrail captures management API activity, not all application requests or S3 object data events. Both deliver to the same audit bucket under separate prefixes:

- `cloudtrail/AWSLogs/<account-id>/...`
- `AWSLogs/<account-id>/...` for VPC Flow Logs

The S3 bucket policy grants each AWS delivery service write access only to its corresponding prefix and constrains the source account or trail ARN. It denies non-TLS requests to the bucket. The account owner remains responsible for IAM read permissions, access monitoring, and incident response.

## Safe evolution

1. Add a workload security group and private endpoints only for a named workload.
2. Model required egress explicitly; review data-exfiltration and endpoint costs.
3. Introduce organization-level identity, SCPs, and delegated security services in a separate module after identifying the management account and ownership model.
4. Replace lab retention with documented legal and operational requirements.
5. Use a remote backend and a release process before any shared deployment.

The plan guard allowlist forces these expansions to be reviewed in code before they can pass the gate.
