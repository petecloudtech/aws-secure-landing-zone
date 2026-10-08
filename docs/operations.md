# Operator notes

## Before planning

1. Use a disposable AWS lab account. Check the active caller identity with `aws sts get-caller-identity` and enter its 12-digit account ID in an ignored `terraform.tfvars`.
2. Look for existing CloudTrail trails and account budgets. This code creates an additional trail and an account-wide budget; existing audit architecture may make it inappropriate to apply.
3. Read current AWS prices for CloudTrail, VPC Flow Logs, S3, and Budgets in the selected region. The defaults are a cost-conscious sample, not a zero-cost guarantee.
4. Set an email that you control. Budget notifications must reach a real owner.
5. For shared use, configure a protected remote state backend and locking before the first apply. Keep state and plan files out of Git.

## Review process

Run `terraform fmt -check -recursive terraform`, `terraform init -backend=false`, and `terraform validate`. An actual plan requires AWS credentials. Save the plan, inspect its diff and estimated resources, convert it with `terraform show -json`, and run `scripts/plan_guard.py`. The gate's allowlist intentionally blocks new resource types and deletion/replacement; a reviewed change requires a deliberate update to the gate and its tests. The gate cannot estimate price or verify live delivery of logs.

## Post-deployment checks, if used later

These checks have **not** been run for this portfolio project.

1. Confirm the correct AWS account and region in the applied state.
2. Check CloudTrail trail status and inspect a recent management event in the audit bucket.
3. Generate a benign VPC action, then check Flow Log delivery under the expected `AWSLogs/` prefix. Delivery is asynchronous.
4. Check bucket public access, encryption, versioning, policy, and object lifecycle in AWS.
5. Confirm both budget notifications list the intended email. Do not wait for a cost threshold merely to test the email.
6. Review daily costs during the lab and stop/remove resources when finished.

## Retirement

Preserve audit evidence according to your retention obligations before removing resources. The bucket uses `force_destroy = false`; a nonempty bucket prevents Terraform from deleting it. Versioning means old versions may also need explicit handling. The plan guard rejects deletes, so retirement requires a deliberate manual review rather than a routine guarded apply. Never weaken retention or delete logs solely to make a demo teardown convenient.
