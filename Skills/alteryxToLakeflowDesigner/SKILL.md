---
name: alteryx-to-lakeflow-designer
description: Analyze and migrate Alteryx Designer workflows (.yxmd and .yxmc) to Databricks Lakeflow Designer visual data prep. Use for migration assessments, source-readiness planning, Designer implementation, and reconciliation. Do not use for requests that specifically require PySpark notebooks or Lakeflow Spark Declarative Pipelines instead of Designer.
---

# Alteryx to Lakeflow Designer

Migrate the workflow's business behavior, not its canvas layout. Separate data onboarding, visual transformation, outputs, and operational side effects before building anything.

Resolve all relative script and reference paths from the directory containing this `SKILL.md`.

## Outcomes

Depending on the request, produce one or more of:

- a workflow inventory and source-readiness assessment;
- a proposed Lakeflow Designer graph with manual prerequisites;
- an implemented visual data prep;
- reconciliation results against a frozen Alteryx baseline;
- a productionization plan using Lakeflow Jobs, Git, and Declarative Automation Bundles.

Do not claim a workflow is migrated when required sources are unavailable, manual nodes are unresolved, or validation has not been run. Missing access does not block an assessment or design.

## Workflow

### 1. Inventory before translating

Run the deterministic inventory script on every supplied workflow and macro:

```bash
python3 scripts/inventory_alteryx.py <workflow-or-directory> --format markdown
```

Use the XML itself as the source of truth. Identify:

- sources, queries, files, and connection types;
- outputs and write modes;
- transformations, branches, and joins;
- referenced macros and interface tools;
- external actions such as HTTP calls, email, commands, and file delivery;
- embedded usernames, passwords, tokens, or connection material.

Use the inventory's effective enabled state: a node inside a disabled Tool Container is
inactive even when the node itself has no disabled flag. Keep inactive nodes in the
assessment, but do not translate them into the active Designer graph unless the user
explicitly asks to restore that behavior. Inspect workflow-level Events as well as tools.

Never copy discovered credentials into generated code, prompts, reports, or Designer operators. Report their presence, recommend rotation when appropriate, and use Unity Catalog connections or Databricks secrets.

### 2. Classify every dependency

Classify each dependency as:

- **Ready**: already a Unity Catalog table, view, or governed Volume file.
- **Connect**: ingest with Lakeflow Connect or an approved connector.
- **Land first**: copy from SMB/UNC, local disk, or another inaccessible system.
- **Convert once**: export proprietary formats such as YXDB or Hyper.
- **Operational**: API, email, command, report rendering, or external file delivery.
- **Manual decision**: behavior cannot be inferred safely from the workflow.

Read [references/sources-and-outputs.md](references/sources-and-outputs.md) whenever a workflow contains files, databases, SharePoint, SFTP, proprietary formats, external outputs, or side effects.

### 3. Design the target before editing the canvas

Describe the target in four layers:

1. **Ingestion**: land source data in Unity Catalog tables or Volumes.
2. **Designer transformation**: clean, join, reshape, calculate, and validate.
3. **Published outputs**: managed tables, materialized views, or governed Volume files.
4. **Job orchestration**: schedules, dependencies, notifications, APIs, and delivery.

Preserve required branch semantics, including Alteryx Filter true/false outputs and Join left-unmatched/matched/right-unmatched outputs. Consolidate repetitive branches when they implement the same rule over different metrics or periods.

Use the smallest graph that remains readable and independently testable. Do not optimize for either a one-to-one tool count or the fewest possible operators.

### 4. Choose operators by semantics

Prefer supported Designer operators when they express the behavior clearly:

| Alteryx behavior | Lakeflow Designer approach |
|---|---|
| Input Data | Source after onboarding to a table, Volume, SharePoint, or supported import |
| Text Input | Enter Data for small constants |
| Select | Select |
| Formula / cleansing | Prepare custom columns and actions |
| Filter | Filter; preserve both outputs when used |
| Join / Join Multiple | Join; verify case, whitespace, null, and unmatched-row behavior |
| Union | Combine, normally union by name with explicit missing-column behavior |
| Summarize | Aggregate |
| Unique | Unique with deterministic ordering when the survivor matters |
| Cross Tab / Transpose | Pivot in pivot or unpivot mode |
| Sort | Sort only when ordering affects semantics or delivery |
| Multi-Row Formula | SQL window functions with explicit partition and order |
| Generate Rows | SQL `sequence`/`explode` or an equivalent governed calendar source |
| Complex custom logic | SQL, Python, or a user-defined operator after built-ins are considered |
| Output Data | Output to a UC table, materialized view, or UC Volume file |

Use AI Functions only for genuinely semantic or generative work where deterministic SQL, a lookup table, or regular expressions are insufficient. Do not introduce AI merely because the migration is being performed by an AI assistant.

Read [references/tool-mapping.md](references/tool-mapping.md) for detailed mappings, macros, interface tools, predictive/spatial tools, and manual boundaries.

### 5. Build with supported Designer behavior

Use Genie Code to create and edit operators on the Designer canvas. Prefer the documented public operator behavior over assumptions about exported notebook internals.

Only generate or modify raw `.designer.ipynb` serialization when the user explicitly requests artifact generation and the structure has been verified against a current workspace export. Treat cell templates, port names, and template versions as version-specific. Validate the result by importing and opening it in Designer.

Read [references/designer-authoring.md](references/designer-authoring.md) before implementing or generating a Designer artifact.

At handoff, state the highest validation stage actually reached: generated, imported and
opened, previewed, fully run, or reconciled. Report later stages as outstanding rather than
using notebook execution metadata as a proxy for Designer validation.

### 6. Handle side effects deliberately

Do not silently translate operational actions into ordinary data operators.

- Prefer separate Lakeflow Job tasks for SOAP/REST calls, email, commands, and file delivery.
- Make retries idempotent and persist delivery state in Delta rather than Excel files.
- If a Python operator or user-defined operator performs a side effect, guard it with `config["is_preview"]` so previews do not send messages or mutate external systems.
- Do not omit Alteryx Block Until Done until its ordering purpose is understood. Data dependencies can become graph edges; side-effect ordering belongs in Jobs.

### 7. Validate on a fixed baseline

Expected Alteryx output is preferred but not an unconditional prerequisite. If it is unavailable, establish agreed invariants and capture a representative frozen input/output fixture before production cutover.

Validate schemas, row counts, keys, nulls, branch populations, aggregates, and row-level differences where stable keys exist. Match Alteryx decimal and date semantics explicitly. Never apply a universal percentage tolerance; tolerances must be justified for each business metric.

Read [references/validation.md](references/validation.md) before running reconciliation or declaring completion.

### 8. Productionize

- Store the visual data prep in a Databricks Git folder.
- Parameterize catalogs, schemas, and environment-specific values.
- Schedule it directly or add it as a Visual data prep task in a Lakeflow Job.
- Use task dependencies for ingestion and post-processing.
- Deploy with Declarative Automation Bundles when the workflow is production-bound.
- Retain reconciliation queries or tests that provide ongoing value.

## Completion checklist

- Every Alteryx node is mapped, intentionally omitted, or marked manual with a reason.
- Disabled nodes are identified separately and are not silently reactivated.
- Every source has an owner and onboarding path.
- Credentials and sensitive configuration are not embedded in generated artifacts.
- Join, filter, deduplication, null, case, and ordering semantics are explicit.
- External side effects are isolated, preview-safe, and idempotent.
- Outputs match the agreed consumer contract; Delta is preferred, not forced when inappropriate.
- Final output projections contain no unintended join keys or collision-generated columns.
- Workflow-level Events and other operational actions are mapped to Jobs, retained as explicit follow-up work, or intentionally retired.
- Validation was run on comparable data and material differences are explained.
- The Designer graph opens successfully and a full run completes, or remaining blockers are stated.
