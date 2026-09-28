# GenieCodeSkills — Alteryx Migration

A set of [Databricks Genie Code](https://docs.databricks.com/aws/en/genie-code/skills) agent skills for migrating Alteryx Designer workflows onto Databricks. Each skill is a self-contained `SKILL.md` (plus supporting files) under `Skills/`.

## Skills


| Skill folder                       | Name                                           | Description                                                                                                                                                                                                                                                                                                                         |
| ---------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Skills/alteryxToPythonSpark`      | **Alteryx Migration to PySpark on Databricks** | Converts Alteryx workflows (`.yxmd`, `.yxmc`, `.yxwz`) into Python / PySpark notebooks following a medallion (bronze / silver / gold) layout, with mandatory output validation against an expected result file.                                                                                                                     |
| `Skills/alteryxToLakeflowDesigner` | **alteryx-to-lakeflow-designer**                | Assesses and migrates Alteryx workflows into Databricks **Lakeflow Designer**. Separates source onboarding, visual transformation, governed outputs, operational side effects, and reconciliation instead of performing a brittle tool-for-tool translation. See [`Skills/alteryxToLakeflowDesigner/Samples/`](Skills/alteryxToLakeflowDesigner/Samples/) for regression examples. |
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

### Option 2 — Databricks Git folder

1. In the Databricks UI: **Workspace → Users → **** → .assistant → skills**, create the `.assistant/skills` path if it does not exist.
2. From the Databricks UI, **Add → Git folder** and clone this repo into a scratch location (e.g. `/Workspace/Users/<you>/repos/GenieCodeSkills_AlteryxMigration`).
3. Move (or symlink/copy) each subdirectory under `Skills/` into `…/.assistant/skills/`. Genie Code will pick up changes automatically when you next open the panel.

### Option 3 — UI upload

1. In the Genie Code panel, click **Settings → Open skills folder**. Databricks opens `/Workspace/Users/<you>/.assistant/skills/` (or the shared folder).
2. For each skill in this repo, create a subfolder with the same name and drag-and-drop its `SKILL.md` (plus any subdirectories) into the workspace folder.

### Verify the install

In a Genie Code chat (Agent mode), type `@` — the three skills should appear in the autocomplete list. You can also invoke one directly, e.g. `@alteryx-to-lakeflow-designer assess and migrate this workflow …`.

## Feedback

For feedback, bug reports, or feature requests, reach out to:

- Isaac Rahnema — [isaac.r@databricks.com](mailto:isaac.r@databricks.com)
- Daphne Koch — [daphne.koch@databricks.com](mailto:daphne.koch@databricks.com)
