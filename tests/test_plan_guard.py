"""Synthetic plan tests. These never create AWS resources."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from plan_guard import validate_plan  # noqa: E402


def sample_plan() -> dict:
    types_and_values = [
        ("aws_vpc", {}),
        ("aws_subnet", {"map_public_ip_on_launch": False}),
        ("aws_subnet", {"map_public_ip_on_launch": False}),
        ("aws_route_table", {"route": []}),
        ("aws_route_table", {"route": []}),
        ("aws_route_table_association", {}),
        ("aws_route_table_association", {}),
        ("aws_s3_bucket", {"force_destroy": False}),
        (
            "aws_s3_bucket_public_access_block",
            {
                "block_public_acls": True,
                "block_public_policy": True,
                "ignore_public_acls": True,
                "restrict_public_buckets": True,
            },
        ),
        ("aws_s3_bucket_ownership_controls", {"rule": [{"object_ownership": "BucketOwnerEnforced"}]}),
        (
            "aws_s3_bucket_server_side_encryption_configuration",
            {"rule": [{"apply_server_side_encryption_by_default": [{"sse_algorithm": "AES256"}]}]},
        ),
        ("aws_s3_bucket_versioning", {"versioning_configuration": [{"status": "Enabled"}]}),
        ("aws_s3_bucket_lifecycle_configuration", {}),
        ("aws_s3_bucket_policy", {}),
        (
            "aws_cloudtrail",
            {
                "is_multi_region_trail": True,
                "include_global_service_events": True,
                "enable_log_file_validation": True,
                "event_selector": [{"include_management_events": True, "read_write_type": "All"}],
            },
        ),
        ("aws_flow_log", {"traffic_type": "ALL", "log_destination_type": "s3"}),
        (
            "aws_budgets_budget",
            {"budget_type": "COST", "time_unit": "MONTHLY", "notification": [{}, {}]},
        ),
    ]
    resources = [
        {"mode": "managed", "type": resource_type, "values": values}
        for resource_type, values in types_and_values
    ]
    return {"planned_values": {"root_module": {"resources": resources}}, "resource_changes": []}


class PlanGuardTest(unittest.TestCase):
    def test_valid_reference_baseline(self) -> None:
        self.assertEqual(validate_plan(sample_plan()), [])

    def test_rejects_internet_gateway_addition(self) -> None:
        plan = sample_plan()
        plan["resource_changes"].append(
            {
                "mode": "managed",
                "address": "aws_internet_gateway.unexpected",
                "type": "aws_internet_gateway",
                "change": {"actions": ["create"]},
            }
        )
        self.assertTrue(any("outside the approved baseline" in e for e in validate_plan(plan)))

    def test_rejects_deletion(self) -> None:
        plan = sample_plan()
        plan["resource_changes"].append(
            {
                "mode": "managed",
                "address": "aws_vpc.foundation",
                "type": "aws_vpc",
                "change": {"actions": ["delete"]},
            }
        )
        self.assertTrue(any("deletion or replacement" in e for e in validate_plan(plan)))

    def test_rejects_public_subnet(self) -> None:
        plan = sample_plan()
        next(r for r in plan["planned_values"]["root_module"]["resources"] if r["type"] == "aws_subnet")[
            "values"
        ]["map_public_ip_on_launch"] = True
        self.assertTrue(any("public IP" in e for e in validate_plan(plan)))

    def test_rejects_disabled_trail_validation(self) -> None:
        plan = sample_plan()
        next(r for r in plan["planned_values"]["root_module"]["resources"] if r["type"] == "aws_cloudtrail")[
            "values"
        ]["enable_log_file_validation"] = False
        self.assertTrue(any("validation" in e for e in validate_plan(plan)))

    def test_rejects_missing_audit_controls(self) -> None:
        plan = sample_plan()
        plan["planned_values"]["root_module"]["resources"] = [
            r for r in plan["planned_values"]["root_module"]["resources"] if r["type"] != "aws_s3_bucket_policy"
        ]
        self.assertTrue(any("aws_s3_bucket_policy" in e for e in validate_plan(plan)))

    def test_input_requires_terraform_json_shape(self) -> None:
        self.assertTrue(validate_plan({}))


if __name__ == "__main__":
    unittest.main()
