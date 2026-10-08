# Security decisions

| Risk or goal | Control in this reference project | Limit or tradeoff |
| --- | --- | --- |
| Applying to the wrong account | Required 12-digit `expected_account_id` and provider `allowed_account_ids` | Caller still needs to verify role, region, and permissions |
| Accidental public workload exposure | Private subnets, `map_public_ip_on_launch = false`, no IGW/NAT, local-only routes | No application traffic can reach external services without a future reviewed change |
| Public audit bucket | Four S3 Public Access Block settings and bucket-owner-enforced ownership | Account-level S3 public access controls remain outside this module |
| Unencrypted or intercepted logs | Explicit SSE-S3 default encryption and deny non-TLS bucket policy | SSE-S3 does not provide customer-controlled KMS keys or key separation |
| Audit log tampering | Versioning, `force_destroy = false`, CloudTrail log-file validation | No Object Lock, immutable retention, or separate security account; administrator access can still affect logs |
| Confused-deputy writes | CloudTrail exact SourceArn; Flow Logs SourceAccount and regional Logs SourceArn wildcard | Regional wildcard is required for delivery but is broader than an individual flow log ARN |
| Unbounded log storage | 90-day current-object expiration and 30-day noncurrent-version expiration | May be too short for compliance or forensics; set a documented retention policy |
| Surprise charges | No NAT, EC2, load balancers, RDS, EKS, or interface endpoints; budget alert and plan allowlist | Audit services still cost money; budget alerts do not stop spend |
| Dangerous changes | Local plan guard rejects deletion/replacement, new resource types, and selected weakened controls | The guard is narrow; human review and security scanning are still required |

## Review of exclusions

This module does not edit an existing account's IAM password policy, S3 account-level public access, default VPC, root MFA, or Organization controls. These are high-impact account-wide settings that should be imported and governed deliberately. It does not grant read access to audit logs beyond whatever authorized principals already exist in the account; a production logging account would use a separate access model.
