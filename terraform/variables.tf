variable "aws_region" {
  description = "Home region for this single-account reference foundation."
  type        = string
  default     = "us-east-2"
}

variable "expected_account_id" {
  description = "12-digit AWS account ID. Provider refuses to operate in any other account."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.expected_account_id))
    error_message = "expected_account_id must be a 12-digit AWS account ID."
  }
}

variable "notification_email" {
  description = "Email address for the account-wide AWS Budget alerts."
  type        = string

  validation {
    condition     = can(regex("^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$", var.notification_email))
    error_message = "notification_email must look like an email address."
  }
}

variable "project_name" {
  description = "Short lowercase name used in resource names and tags."
  type        = string
  default     = "secure-foundation"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,19}$", var.project_name))
    error_message = "project_name must be 3-20 lowercase letters, digits, or hyphens and start with a letter."
  }
}

variable "environment" {
  description = "Environment label for names and tags."
  type        = string
  default     = "lab"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,9}$", var.environment))
    error_message = "environment must be 2-10 lowercase letters, digits, or hyphens and start with a letter."
  }
}

variable "vpc_cidr" {
  description = "IPv4 /16 VPC CIDR. Two /24 subnets are derived from it."
  type        = string
  default     = "10.42.0.0/16"

  validation {
    condition     = can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}/16$", var.vpc_cidr)) && can(cidrsubnet(var.vpc_cidr, 8, 1))
    error_message = "vpc_cidr must be a valid IPv4 /16 network."
  }
}

variable "monthly_budget_usd" {
  description = "Account-wide monthly budget alert amount in USD; it does not cap spend."
  type        = number
  default     = 20

  validation {
    condition     = var.monthly_budget_usd >= 1 && var.monthly_budget_usd <= 10000
    error_message = "monthly_budget_usd must be between 1 and 10000."
  }
}

variable "log_retention_days" {
  description = "Days to retain current log objects in S3. Set for your actual retention requirements."
  type        = number
  default     = 90

  validation {
    condition     = var.log_retention_days >= 30 && var.log_retention_days <= 3650
    error_message = "log_retention_days must be between 30 and 3650."
  }
}
