# Staged Alteryx to Lakeflow Designer migration

This pack separates migration planning from Lakeflow Designer implementation so a human can
review source contracts, target behavior, and validation before the canvas is changed.

```text
Alteryx files
    ↓
alteryx-migration-planner
    ├── <workflow>.migration-plan.ipynb   human review and read-only profiling
    └── <workflow>.migration-plan.yaml    versioned machine contract
              ↓ explicit human approval
alteryx-to-lakeflow-designer-builder
    └── approved Designer branches + structural/data validation
```

## Skills

| Folder | Skill | Responsibility |
|---|---|---|
| `alteryxMigrationPlanner/` | `alteryx-migration-planner` | Inventory, planning notebook, YAML contract, approval questions; never builds Designer |
| `alteryxToLakeflowDesignerBuilder/` | `alteryx-to-lakeflow-designer-builder` | Validates an approved plan, builds named branches, and reports validation status |

Both skills use migration-plan schema version `1`. The notebook is explanatory; YAML is the
handoff contract. Neither a notebook edit nor `status: approved` replaces explicit user
approval in the current build request.

## Install

Install both skill directories directly under your personal or shared Genie Code skills
folder. With the Databricks CLI from the repository root:

```bash
databricks auth login --host https://<your-workspace>.cloud.databricks.com
DEST=/Users/$(databricks current-user me | jq -r .userName)/.assistant/skills

databricks workspace import-dir \
  Skills/alteryxDesignerStagedMigration/alteryxMigrationPlanner \
  "$DEST/alteryxMigrationPlanner" --overwrite

databricks workspace import-dir \
  Skills/alteryxDesignerStagedMigration/alteryxToLakeflowDesignerBuilder \
  "$DEST/alteryxToLakeflowDesignerBuilder" --overwrite
```

After updating installed skill files, start a fresh Genie Code chat or explicitly reload the
skill. Confirm the revision printed at the start of each result.

## 1. Create the review plan

Supply the workflow's parent directory when macros are stored alongside the `.yxmd`.

```text
@alteryx-migration-planner
Assess <workflow-or-directory>. Create a conventional review notebook and schema-version 1
migration-plan YAML. Perform no Designer edits and no external side effects. Stop with the
source/output, graph, and operational decisions requiring approval.
```

Expected outputs:

- `<workflow>.migration-plan.ipynb`
- `<workflow>.migration-plan.yaml`

The notebook may contain read-only profiling cells for approved UC sources. It must not
implement the migrated transformation, publish tables, invoke APIs, or send messages.

## 2. Review and approve

Review source onboarding, macro handling, output contracts, side effects, branch
decomposition, semantic decisions, expected schemas, and validation checks. Ask the planner
to incorporate decisions and regenerate both artifacts. Approval must be explicit, for
example:

```text
I approve the source/output contracts, graph and semantic decisions, and branches
<branch IDs> in migration plan <plan ID>. Update the plan to approved and validate it.
```

Do not approve a plan with blocking unresolved items or stale workflow hashes.

## 3. Build an approved branch

Use a fresh builder chat and name the exact branch scope:

```text
@alteryx-to-lakeflow-designer-builder
Using <migration-plan.yaml>, build approved branch <branch ID>. I explicitly approve this
Designer mutation. Do not activate schedules, delivery, APIs, or messages. Stop after
structural validation and available previews.
```

Repeat by branch for large workflows. A small, low-risk workflow may approve and build all
branches together.

## 4. Validate

```text
@alteryx-to-lakeflow-designer-builder
Mode: Validate. Compare the built branches in <migration-plan.yaml> with the approved plan
and frozen Alteryx baseline. Report differences; do not redesign or productionize.
```

Generated, imported, opened, previewed, fully run, and reconciled are separate validation
stages. Production schedules and external side effects require a later explicit request.

## Local checks

```bash
python3 alteryxMigrationPlanner/scripts/inventory_alteryx.py \
  <workflow-or-directory> --format markdown

python3 alteryxMigrationPlanner/scripts/validate_migration_plan.py \
  <workflow>.migration-plan.yaml
```

The same plan validator is bundled with the builder so each skill remains independently
installable.
