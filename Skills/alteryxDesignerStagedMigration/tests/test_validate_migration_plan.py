import importlib.util
import unittest
from pathlib import Path


PACK = Path(__file__).parents[1]
PLANNER_SCRIPT = (
    PACK / "alteryxMigrationPlanner" / "scripts" / "validate_migration_plan.py"
)
BUILDER_SCRIPT = (
    PACK
    / "alteryxToLakeflowDesignerBuilder"
    / "scripts"
    / "validate_migration_plan.py"
)
SPEC = importlib.util.spec_from_file_location("validate_migration_plan", PLANNER_SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


def plan(status="draft"):
    return {
        "schema_version": 1,
        "plan_id": "example-plan",
        "status": status,
        "planner": {
            "skill": "alteryx-migration-planner",
            "revision": "2026-09-29-plan-v1",
        },
        "workflow": {
            "primary_path": "/workspace/example.yxmd",
            "sha256": "a" * 64,
            "macros": [],
        },
        "sources": [],
        "outputs": [],
        "events": [],
        "branches": [],
        "node_mappings": [],
        "semantic_decisions": [],
        "validation": {"structural": [], "data": []},
        "unresolved": [],
        "approvals": {
            "source_output_contracts": "pending",
            "graph_and_semantics": "pending",
        },
    }


class MigrationPlanValidationTest(unittest.TestCase):
    def test_valid_draft(self):
        self.assertEqual(validator.validate_plan(plan()), [])

    def test_approved_plan_requires_approvals_and_approved_branches(self):
        approved = plan("approved")
        approved["branches"] = [
            {
                "id": "output-a",
                "selected_for_build": True,
                "approval": "pending",
            }
        ]

        errors = validator.validate_plan(approved)

        self.assertIn(
            "approved plans require approvals.source_output_contracts=approved",
            errors,
        )
        self.assertIn(
            "approved plans require approvals.graph_and_semantics=approved", errors
        )
        self.assertIn(
            "branches[0] is selected_for_build but not approved", errors
        )

    def test_valid_approved_plan(self):
        approved = plan("approved")
        approved["approvals"] = {
            "source_output_contracts": "approved",
            "graph_and_semantics": "approved",
        }
        approved["sources"] = [
            {
                "id": "source-a",
                "status": "approved",
                "target": {"kind": "table", "identifier": "catalog.schema.input"},
            }
        ]
        approved["outputs"] = [
            {
                "id": "output-a",
                "status": "approved",
                "target": {"kind": "table", "identifier": "catalog.schema.output"},
            }
        ]
        approved["branches"] = [
            {
                "id": "branch-a",
                "source_ids": ["source-a"],
                "output_ids": ["output-a"],
                "selected_for_build": True,
                "approval": "approved",
            }
        ]

        self.assertEqual(validator.validate_plan(approved), [])

    def test_approved_plan_rejects_unknown_source_and_output_references(self):
        approved = plan("approved")
        approved["approvals"] = {
            "source_output_contracts": "approved",
            "graph_and_semantics": "approved",
        }
        approved["branches"] = [
            {
                "id": "branch-a",
                "source_ids": ["missing-source"],
                "output_ids": ["missing-output"],
                "selected_for_build": True,
                "approval": "approved",
            }
        ]

        errors = validator.validate_plan(approved)

        self.assertIn(
            "branches[0] references unknown source_id 'missing-source'", errors
        )
        self.assertIn(
            "branches[0] references unknown output_id 'missing-output'", errors
        )

    def test_approved_plan_rejects_unresolved_source_target(self):
        approved = plan("approved")
        approved["approvals"] = {
            "source_output_contracts": "approved",
            "graph_and_semantics": "approved",
        }
        approved["sources"] = [
            {"id": "source-a", "status": "pending", "target": {}}
        ]
        approved["branches"] = [
            {
                "id": "branch-a",
                "source_ids": ["source-a"],
                "output_ids": [],
                "selected_for_build": True,
                "approval": "approved",
            }
        ]

        errors = validator.validate_plan(approved)

        self.assertIn(
            "selected branch 'branch-a' requires source 'source-a' to have status approved",
            errors,
        )
        self.assertIn(
            "selected branch 'branch-a' requires source 'source-a' to have target.kind and target.identifier",
            errors,
        )

    def test_approved_plan_rejects_blocking_unresolved_items(self):
        approved = plan("approved")
        approved["approvals"] = {
            "source_output_contracts": "approved",
            "graph_and_semantics": "approved",
        }
        approved["unresolved"] = [
            {"id": "missing-source", "blocking": True}
        ]

        self.assertIn(
            "approved plans cannot contain blocking unresolved items",
            validator.validate_plan(approved),
        )

    def test_planner_and_builder_bundle_same_validator(self):
        self.assertEqual(PLANNER_SCRIPT.read_bytes(), BUILDER_SCRIPT.read_bytes())


if __name__ == "__main__":
    unittest.main()
