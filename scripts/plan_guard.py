#!/usr/bin/env python3
"""Reject unexpected or insecure changes in a Terraform JSON plan.

This is an additional portfolio guard, not a complete security scanner or a
substitute for reviewing a real plan and AWS account context.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ALLOWED_RESOURCE_TYPES = frozenset(
    {
        "aws_vpc",
        "aws_subnet",
        "aws_route_table",
        "aws_route_table_association",
        "aws_s3_bucket",
        "aws_s3_bucket_public_access_block",
        "aws_s3_bucket_ownership_controls",
        "aws_s3_bucket_server_side_encryption_configuration",
        "aws_s3_bucket_versioning",
        "aws_s3_bucket_lifecycle_configuration",
        "aws_s3_bucket_policy",
        "aws_cloudtrail",
        "aws_flow_log",
        "aws_budgets_budget",
    }
)

REQUIRED_COUNTS = {
    "aws_vpc": 1,
    "aws_subnet": 2,
    "aws_route_table": 2,
    "aws_route_table_association": 2,
    "aws_s3_bucket": 1,
    "aws_s3_bucket_public_access_block": 1,
    "aws_s3_bucket_ownership_controls": 1,
    "aws_s3_bucket_server_side_encryption_configuration": 1,
    "aws_s3_bucket_versioning": 1,
    "aws_s3_bucket_lifecycle_configuration": 1,
    "aws_s3_bucket_policy": 1,
    "aws_cloudtrail": 1,
    "aws_flow_log": 1,
    "aws_budgets_budget": 1,
}


def first_block(value: Any) -> dict[str, Any]:
    """Normalize Terraform's JSON representation of a nested block."""
    if isinstance(value, list):
        return value[0] if value and isinstance(value[0], dict) else {}
    return value if isinstance(value, dict) else {}


def managed_resources(module: dict[str, Any]) -> list[dict[str, Any]]:
    found = [r for r in module.get("resources", []) if r.get("mode") == "managed"]
    for child in module.get("child_modules", []):
        found.extend(managed_resources(child))
    return found


def validate_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    root = plan.get("planned_values", {}).get("root_module")
    changes = plan.get("resource_changes")
    if not isinstance(root, dict) or not isinstance(changes, list):
        return ["Expected terraform show -json output with planned_values and resource_changes."]

    for item in changes:
        if item.get("mode") != "managed":
            continue
        name = item.get("address", "<unknown>")
        resource_type = item.get("type", "<unknown>")
        actions = item.get("change", {}).get("actions", [])
        if "delete" in actions:
            errors.append(f"{name}: deletion or replacement requires manual review.")
        if resource_type not in ALLOWED_RESOURCE_TYPES:
            errors.append(f"{name}: resource type {resource_type} is outside the approved baseline.")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in managed_resources(root):
        grouped[item.get("type", "<unknown>")].append(item.get("values", {}))
    for resource_type in grouped:
        if resource_type not in ALLOWED_RESOURCE_TYPES:
            errors.append(f"Planned values include unexpected resource type {resource_type}.")
    for resource_type, count in REQUIRED_COUNTS.items():
        actual = len(grouped[resource_type])
        if actual != count:
            errors.append(f"Expected {count} {resource_type} resource(s), found {actual}.")

    if len(grouped["aws_s3_bucket"]) == 1:
        if grouped["aws_s3_bucket"][0].get("force_destroy") is not False:
            errors.append("Audit bucket must have force_destroy=false.")

    for subnet in grouped["aws_subnet"]:
        if subnet.get("map_public_ip_on_launch") is not False:
            errors.append("Every subnet must disable public IP assignment.")

    for route_table in grouped["aws_route_table"]:
        if route_table.get("route") not in (None, []):
            errors.append("Private route tables must have no non-local routes.")

    if len(grouped["aws_s3_bucket_public_access_block"]) == 1:
        access = grouped["aws_s3_bucket_public_access_block"][0]
        for key in (
            "block_public_acls",
            "block_public_policy",
            "ignore_public_acls",
            "restrict_public_buckets",
        ):
            if access.get(key) is not True:
                errors.append(f"Audit bucket must set {key}=true.")

    if len(grouped["aws_s3_bucket_ownership_controls"]) == 1:
        ownership = first_block(grouped["aws_s3_bucket_ownership_controls"][0].get("rule"))
        if ownership.get("object_ownership") != "BucketOwnerEnforced":
            errors.append("Audit bucket must use BucketOwnerEnforced ownership.")

    if len(grouped["aws_s3_bucket_server_side_encryption_configuration"]) == 1:
        encryption = first_block(
            grouped["aws_s3_bucket_server_side_encryption_configuration"][0].get("rule")
        )
        default = first_block(encryption.get("apply_server_side_encryption_by_default"))
        if default.get("sse_algorithm") != "AES256":
            errors.append("Audit bucket must enable SSE-S3 AES256 encryption.")

    if len(grouped["aws_s3_bucket_versioning"]) == 1:
        versioning = first_block(grouped["aws_s3_bucket_versioning"][0].get("versioning_configuration"))
        if versioning.get("status") != "Enabled":
            errors.append("Audit bucket versioning must be enabled.")

    if len(grouped["aws_cloudtrail"]) == 1:
        trail = grouped["aws_cloudtrail"][0]
        if trail.get("is_multi_region_trail") is not True:
            errors.append("CloudTrail must cover all regions.")
        if trail.get("include_global_service_events") is not True:
            errors.append("CloudTrail must include global service events.")
        if trail.get("enable_log_file_validation") is not True:
            errors.append("CloudTrail log file validation must be enabled.")
        selector = first_block(trail.get("event_selector"))
        if selector.get("include_management_events") is not True or selector.get("read_write_type") != "All":
            errors.append("CloudTrail must include read and write management events.")

    if len(grouped["aws_flow_log"]) == 1:
        flow = grouped["aws_flow_log"][0]
        if flow.get("traffic_type") != "ALL" or flow.get("log_destination_type") != "s3":
            errors.append("VPC Flow Logs must capture ALL traffic to S3.")

    if len(grouped["aws_budgets_budget"]) == 1:
        budget = grouped["aws_budgets_budget"][0]
        if budget.get("budget_type") != "COST" or budget.get("time_unit") != "MONTHLY":
            errors.append("An account-wide monthly cost budget is required.")
        if len(budget.get("notification") or []) < 2:
            errors.append("Budget must send at least two notifications.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan_json", help="Path from 'terraform show -json PLAN', or '-' for stdin")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.plan_json == "-" else Path(args.plan_json).read_text()
        plan = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read JSON plan: {exc}", file=sys.stderr)
        return 2
    errors = validate_plan(plan)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: planned resources match the reviewed low-footprint security baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
