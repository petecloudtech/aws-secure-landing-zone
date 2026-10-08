data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  zones       = slice(data.aws_availability_zones.available.names, 0, 2)
  subnets     = {
    for index, zone in local.zones : zone => cidrsubnet(var.vpc_cidr, 8, index)
  }
  trail_name  = "${local.name_prefix}-management"
  trail_arn   = "arn:${data.aws_partition.current.partition}:cloudtrail:${var.aws_region}:${data.aws_caller_identity.current.account_id}:trail/${local.trail_name}"
  logs_arn    = "arn:${data.aws_partition.current.partition}:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
}
