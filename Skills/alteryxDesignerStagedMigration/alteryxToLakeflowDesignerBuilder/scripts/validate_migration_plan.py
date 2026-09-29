#!/usr/bin/env python3
"""Validate the staged Alteryx migration-plan YAML contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on the host environment
    raise SystemExit(
        "PyYAML is required to validate migration plans. Install it in the authoring environment."
    ) from exc


REQUIRED_KEYS = {
    "schema_version",
    "plan_id",
    "status",
    "planner",
    "workflow",
    "sources",
    "outputs",
    "events",
    "branches",
    "node_mappings",
    "semantic_decisions",
    "validation",
    "unresolved",
    "approvals",
}
LIST_KEYS = {
    "sources",
    "outputs",
    "events",
    "branches",
    "node_mappings",
    "semantic_decisions",
    "unresolved",
}
VALID_STATUSES = {"draft", "approved", "superseded", "rejected"}


def load_plan(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Could not read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc


def validate_plan(plan: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["plan must be a YAML mapping"]

    missing = sorted(REQUIRED_KEYS - set(plan))
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))

    if plan.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(plan.get("plan_id"), str) or not plan.get("plan_id", "").strip():
        errors.append("plan_id must be a non-empty string")
    if plan.get("status") not in VALID_STATUSES:
        errors.append("status must be one of: " + ", ".join(sorted(VALID_STATUSES)))

    for key in LIST_KEYS:
        if key in plan and not isinstance(plan[key], list):
            errors.append(f"{key} must be a list")

    planner = plan.get("planner")
    if not isinstance(planner, dict):
        errors.append("planner must be a mapping")
    else:
        if not planner.get("skill"):
            errors.append("planner.skill is required")
        if not planner.get("revision"):
            errors.append("planner.revision is required")

    workflow = plan.get("workflow")
    if not isinstance(workflow, dict):
        errors.append("workflow must be a mapping")
    else:
        if not workflow.get("primary_path"):
            errors.append("workflow.primary_path is required")
        sha256 = workflow.get("sha256", "")
        if not isinstance(sha256, str) or len(sha256) != 64:
            errors.append("workflow.sha256 must be a 64-character SHA-256 value")
        if not isinstance(workflow.get("macros", []), list):
            errors.append("workflow.macros must be a list")

    validation = plan.get("validation")
    if not isinstance(validation, dict):
        errors.append("validation must be a mapping")

    approvals = plan.get("approvals")
    if not isinstance(approvals, dict):
        errors.append("approvals must be a mapping")
    elif plan.get("status") == "approved":
        if approvals.get("source_output_contracts") != "approved":
            errors.append(
                "approved plans require approvals.source_output_contracts=approved"
            )
        if approvals.get("graph_and_semantics") != "approved":
            errors.append(
                "approved plans require approvals.graph_and_semantics=approved"
            )

    unresolved = plan.get("unresolved", [])
    if plan.get("status") == "approved" and isinstance(unresolved, list):
        blockers = [
            item
            for item in unresolved
            if isinstance(item, dict)
            and (
                item.get("blocking") is True
                or str(item.get("severity", "")).lower() == "blocking"
            )
        ]
        if blockers:
            errors.append("approved plans cannot contain blocking unresolved items")

    branches = plan.get("branches", [])
    if plan.get("status") == "approved" and isinstance(branches, list):
        selected_branches = [
            (index, branch)
            for index, branch in enumerate(branches)
            if isinstance(branch, dict) and branch.get("selected_for_build") is True
        ]
        if not selected_branches:
            errors.append("approved plans require at least one selected branch")

        source_records = plan.get("sources", [])
        output_records = plan.get("outputs", [])
        source_by_id = {
            item.get("id"): item
            for item in source_records
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item.get("id")
        }
        output_by_id = {
            item.get("id"): item
            for item in output_records
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item.get("id")
        }

        for index, branch in enumerate(branches):
            if not isinstance(branch, dict):
                errors.append(f"branches[{index}] must be a mapping")
                continue

            source_ids = branch.get("source_ids", [])
            output_ids = branch.get("output_ids", [])
            if not isinstance(source_ids, list):
                errors.append(f"branches[{index}].source_ids must be a list")
                source_ids = []
            if not isinstance(output_ids, list):
                errors.append(f"branches[{index}].output_ids must be a list")
                output_ids = []

            for source_id in source_ids:
                if source_id not in source_by_id:
                    errors.append(
                        f"branches[{index}] references unknown source_id {source_id!r}"
                    )
            for output_id in output_ids:
                if output_id not in output_by_id:
                    errors.append(
                        f"branches[{index}] references unknown output_id {output_id!r}"
                    )

            if branch.get("selected_for_build") is not True:
                continue
            if branch.get("approval") != "approved":
                errors.append(
                    f"branches[{index}] is selected_for_build but not approved"
                )

            for source_id in source_ids:
                source = source_by_id.get(source_id)
                if source is None:
                    continue
                if source.get("status") != "approved":
                    errors.append(
                        f"selected branch {branch.get('id', index)!r} requires source "
                        f"{source_id!r} to have status approved"
                    )
                target = source.get("target")
                if not isinstance(target, dict) or not target.get("kind") or not target.get("identifier"):
                    errors.append(
                        f"selected branch {branch.get('id', index)!r} requires source "
                        f"{source_id!r} to have target.kind and target.identifier"
                    )

            for output_id in output_ids:
                output = output_by_id.get(output_id)
                if output is None:
                    continue
                if output.get("status") != "approved":
                    errors.append(
                        f"selected branch {branch.get('id', index)!r} requires output "
                        f"{output_id!r} to have status approved"
                    )
                target = output.get("target")
                if not isinstance(target, dict) or not target.get("kind") or not target.get("identifier"):
                    errors.append(
                        f"selected branch {branch.get('id', index)!r} requires output "
                        f"{output_id!r} to have target.kind and target.identifier"
                    )

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plans", nargs="+", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failed = False
    for path in args.plans:
        try:
            plan = load_plan(path)
            errors = validate_plan(plan)
        except ValueError as exc:
            errors = [str(exc)]
        if errors:
            failed = True
            print(f"{path}: invalid", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
        else:
            print(f"{path}: valid")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
