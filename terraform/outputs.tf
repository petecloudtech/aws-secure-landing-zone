output "vpc_id" {
  description = "ID of the isolated VPC."
  value       = aws_vpc.foundation.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs, keyed by availability zone."
  value       = { for zone, subnet in aws_subnet.private : zone => subnet.id }
}

output "audit_bucket_name" {
  description = "S3 bucket for CloudTrail and VPC Flow Logs."
  value       = aws_s3_bucket.audit.id
}

output "management_trail_arn" {
  description = "Multi-region management event trail ARN."
  value       = aws_cloudtrail.management.arn
}

output "vpc_flow_log_id" {
  description = "VPC Flow Log ID."
  value       = aws_flow_log.vpc.id
}
