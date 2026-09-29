# GenieCodeSkills — Alteryx Migration

A set of [Databricks Genie Code](https://docs.databricks.com/aws/en/genie-code/skills) agent skills for migrating Alteryx Designer workflows onto Databricks. Each skill is a self-contained `SKILL.md` (plus supporting files) under `Skills/`.

## Skills


| Skill folder                       | Name                                           | Description                                                                                                                                                                                                                                                                                                                         |
| ---------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Skills/alteryxToPythonSpark`      | **Alteryx Migration to PySpark on Databricks** | Converts Alteryx workflows (`.yxmd`, `.yxmc`, `.yxwz`) into Python / PySpark notebooks following a medallion (bronze / silver / gold) layout, with mandatory output validation against an expected result file.                                                                                                                     |
| `Skills/alteryxToLakeflowDesigner` | **alteryx-to-lakeflow-designer**                | Assesses and migrates Alteryx workflows into Databricks **Lakeflow Designer**. Separates source onboarding, visual transformation, governed outputs, operational side effects, and reconciliation instead of performing a brittle tool-for-tool translation. See [`Skills/alteryxToLakeflowDesigner/Samples/`](Skills/alteryxToLakeflowDesigner/Samples/) for regression examples. |
| `Skills/alteryxDesignerStagedMigration` | **Staged Designer migration pack** | Splits planning and implementation into `alteryx-migration-planner` and `alteryx-to-lakeflow-designer-builder`, connected by a review notebook and versioned YAML plan. See the [pack README](Skills/alteryxDesignerStagedMigration/README.md). |
| `Skills/alteryxToDatabricksSdp`    | **alteryx-to-databricks-sdp**                  | Converts Alteryx workflows into a runnable Databricks **Lakeflow Spark Declarative Pipeline (SDP)** expressed in pure SQL. Emits `CREATE OR REFRESH STREAMING TABLE` / `MATERIALIZED VIEW` files in bronze/silver/gold layers plus a `MANUAL_STEPS.md` for anything that can't be auto-converted.                                   |

## Recommended POC workflow for Lakeflow Designer

Use `alteryx-to-lakeflow-designer` in stages. A single “migrate this workflow” request can be
slow and can force the agent to guess source contracts, missing macro behavior, output
delivery, or side effects. The staged process puts a human decision only where it can change
the result:

```text
assessment → source/output approval → design → graph approval
           → scoped build → structural validation → reconciliation
```

The skill supports five modes: **Assess**, **Design**, **Build**, **Validate**, and
**Productionize**. It stops at the boundary of the requested mode. For complex workflows,
build one output or logical branch at a time; for small low-risk workflows, approve all
branches in the design gate and build them together.

### 1. Run a quick assessment

Provide the parent directory when the workflow references `.yxmc` macros so the skill can
resolve them. Do not upload only the `.yxmd` and expect missing macros to be inferred.

```text
@alteryx-to-lakeflow-designer
Mode: Assess only. Do not create or modify a visual data prep.

Assess <workflow-or-directory>. Report the loaded skill revision, active and inactive nodes,
resolved and missing macros, source readiness, outputs, workflow Events, semantic hotspots,
and a recommended build decomposition. Stop for source/output approval.
```

### 2. Approve the design

```text
@alteryx-to-lakeflow-designer
Mode: Design only. Use the approved source and output decisions from the assessment.

Design the ingestion, Designer transformation, published outputs, and Job orchestration.
Provide the node/pattern mapping, expected output schemas, consolidation rationales, and
validation plan. Do not build yet. Stop for graph approval.
```

### 3. Build a bounded scope

```text
@alteryx-to-lakeflow-designer
Mode: Build. Implement only <approved output or branch> from the approved design.

Do not fabricate Enter Data rows for unavailable sources. Add meaningful Guardrails, preview
available intermediate data, run structural parity checks, and stop with the validation stage
reached and the next branch to request.
```

### 4. Validate before productionizing

```text
@alteryx-to-lakeflow-designer
Mode: Validate. Compare the approved Designer scope with the Alteryx inventory and frozen
baseline. Report structural, schema, population, value, boundary, and operational differences.
Do not redesign or productionize automatically.
```

Only request **Productionize** after the output owner accepts the reconciliation. Enabling
schedules, external file delivery, APIs, or messages remains a separate explicit approval.

### Confirm that an updated skill is loaded

An open Genie Code chat can retain an older skill in its context after the workspace files
change. Start a fresh chat after installing an update, or explicitly ask Genie Code to reload
the skill. The assessment response should report the revision from `SKILL.md`; the current
Lakeflow Designer revision is `2026-09-28-staged-poc-v1`.




## Installing to the Genie Code skills folder

Genie Code looks for skills in one of two workspace folders:

- **Personal (just you):** `/Workspace/Users/<your-email>/.assistant/skills/`
- **Shared (whole workspace):** `/Workspace/.assistant/skills/`

Each skill must live in its own subfolder containing a `SKILL.md` at the root, e.g. `…/.assistant/skills/alteryx-to-lakeflow-designer/SKILL.md`.

You can install via the Databricks CLI, a Git folder, or the UI.

### Option 1 — Databricks CLI (recommended)

Authenticate once, then import each skill folder:

```bash
# Authenticate (one-time)
databricks auth login --host https://<your-workspace>.cloud.databricks.com

# Pick a destination root
DEST=/Users/$(databricks current-user me | jq -r .userName)/.assistant/skills
# or for a shared install:
# DEST=/.assistant/skills

# Import each skill
for skill in alteryxToPythonSpark alteryxToLakeflowDesigner alteryxToDatabricksSdp; do
  databricks workspace import-dir "Skills/$skill" "$DEST/$skill" --overwrite
done
```

The staged Designer pack contains two independently installable skills:

```bash
databricks workspace import-dir \
  Skills/alteryxDesignerStagedMigration/alteryxMigrationPlanner \
  "$DEST/alteryxMigrationPlanner" --overwrite
databricks workspace import-dir \
  Skills/alteryxDesignerStagedMigration/alteryxToLakeflowDesignerBuilder \
  "$DEST/alteryxToLakeflowDesignerBuilder" --overwrite
```

### Option 2 — Databricks UI upload (one skill)

Use this option to install only the Lakeflow Designer skill without cloning the whole
repository.

1. Download or check out
   `Skills/alteryxToLakeflowDesigner/` from this repository to your computer.
2. Open Genie Code in the Databricks workspace, select **Settings** (the gear icon),
   and click **Open skills folder**. This opens your personal skills directory:
   `/Workspace/Users/<your-email>/.assistant/skills/`.
3. In the workspace file browser, create a folder named
   `alteryxToLakeflowDesigner` under `skills`.
4. Upload the contents of the local `alteryxToLakeflowDesigner` folder into the new
   workspace folder. If your workspace supports folder upload, upload the folder in one
   operation. Otherwise create the `references` and `scripts` subfolders in the UI and
   upload their files separately. Preserve this structure:

   ```text
   .assistant/skills/alteryxToLakeflowDesigner/
   ├── SKILL.md
   ├── references/
   │   ├── designer-authoring.md
   │   ├── sources-and-outputs.md
   │   ├── tool-mapping.md
   │   └── validation.md
   └── scripts/
       └── inventory_alteryx.py
   ```

   The `Samples/` folder is useful for regression testing but is not required to run the
   skill.
5. To make the skill available to the whole workspace instead, create the same folder at
   `/Workspace/.assistant/skills/alteryxToLakeflowDesigner/`. You need permission to
   create and manage files there; confirm that intended users have read access.
6. Start a new Genie Code Agent-mode chat after the upload. Existing chats can retain an
   older copy of a skill in their context.

### Option 3 — Databricks Git folder

1. From the Databricks UI, select **Workspace → Add → Git folder** and clone this repo
   into a scratch location such as
   `/Workspace/Users/<your-email>/repos/GenieCodeSkills_AlteryxMigration`.
2. Create the personal path
   `/Workspace/Users/<your-email>/.assistant/skills/` or the shared path
   `/Workspace/.assistant/skills/` if it does not exist.
3. Copy the required skill folder from `Skills/` into the chosen `skills` directory.
   Keep `SKILL.md` at the root of that copied folder and preserve all referenced
   subdirectories.
4. Pull future repository changes into the Git folder, then copy the updated skill files
   to the discovery directory and start a new Genie Code chat.

### Verify the install

In a new Genie Code chat (Agent mode), type `@` and confirm that
`alteryx-to-lakeflow-designer` appears in autocomplete. You can invoke it directly, for
example: `@alteryx-to-lakeflow-designer assess this workflow …`.

## Feedback

For feedback, bug reports, or feature requests, reach out to:

- Isaac Rahnema — [isaac.r@databricks.com](mailto:isaac.r@databricks.com)
- Daphne Koch — [daphne.koch@databricks.com](mailto:daphne.koch@databricks.com)
