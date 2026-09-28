# Alteryx to Lakeflow Designer mapping

Use this reference after inventorying the workflow. Map behavior rather than tool names alone: configuration, incoming anchors, outgoing anchors, metadata, and downstream use determine the correct translation.

## Core tools

| Alteryx tool or pattern | Preferred Designer approach | Important checks |
|---|---|---|
| Input Data: database | Source from a UC table/view after federation or ingestion | Preserve query predicates, snapshot timing, and source timezone |
| Input Data: file | Source from a UC Volume, managed SharePoint ingestion, or uploaded file | Preserve sheet, delimiter, encoding, header, and malformed-row behavior |
| Output Data | Output table, materialized view, or Volume file | Preserve overwrite/append/upsert intent and consumer contract |
| Browse | Omit | Designer provides previews; retain only useful documentation |
| Text Input | Enter Data | Keep small; use a governed reference table for maintained mappings |
| Select | Select | Preserve drop, rename, reorder, and type changes |
| Formula | Prepare custom columns | Translate Alteryx null, boolean, string, and date semantics explicitly |
| Data Cleansing | Prepare | Confirm whether case conversion applies to values, column names, or both |
| Filter | Filter | Preserve true and false branches if either is consumed |
| Sort | Sort | Retain only when ordering affects windows, survivor selection, or output |
| Sample / First N | Limit or SQL | Define deterministic order before first/last selections |
| Record ID | SQL `row_number()` | Require a deterministic ordering expression |
| Unique | Unique | Specify keys and ordering when the retained record matters |
| Union | Combine | Choose by-name/by-position behavior and missing-column handling deliberately |
| Join | Join | Preserve join keys, comparison normalization, join type, and unmatched branches |
| Join Multiple | Multi-input Join or staged Joins | Avoid changing multiplicity; profile duplicate keys first |
| Append Fields | Cross join in SQL when required | Confirm one side is intentionally small and cardinality is expected |
| Find Replace | Join to a reference table, or Prepare for a tiny stable mapping | Preserve replace-found versus append-field behavior |
| Summarize | Aggregate | Preserve group keys, null handling, concatenation order, and output types |
| Cross Tab | Pivot: rows to columns | Preserve aggregation and generated column-name behavior |
| Transpose | Pivot: columns to rows | Preserve identifier columns and name/value types |
| Text To Columns | Prepare for fixed columns; SQL `explode` for rows | Confirm delimiter, quoting, overflow, and null behavior |
| DateTime | Prepare | Confirm timezone, locale, parsing pattern, and invalid-value behavior |
| RegEx | Prepare or SQL | Preserve regex dialect, capture group, case sensitivity, and tokenize mode |
| Multi-Row Formula | SQL window functions | Define partition, ordering, frame, and missing previous/next row behavior |
| Running Total | SQL window aggregation | Match partition, ordering, and window frame |
| Generate Rows | SQL `sequence`/`explode` or governed calendar table | Confirm bounds, inclusivity, interval, and row growth |
| Dynamic Rename | Select/Prepare with an explicit schema | Prefer stable schemas; flag data-dependent column names |
| Field Info | Assessment or schema metadata query | Usually not part of the production data path |
| Block Until Done | Graph or Job dependencies | Do not omit until side-effect ordering is understood |

## Branch equivalence

### Filter

Alteryx Filter exposes True and False anchors. Designer Filter can expose included and excluded rows. Wire both when downstream nodes consume both. Remember that SQL null predicates are not true; verify whether nulls belong to the excluded branch.

### Join

Alteryx Join exposes left-unmatched, matched, and right-unmatched anchors. Configure Designer Join outputs or explicit downstream branches to preserve only the anchors actually consumed. Validate:

- duplicate-key multiplication;
- null-key matching;
- string case and trimming;
- right-side duplicate column names;
- output field selection and renames.

## SQL candidates

Use SQL when it materially improves correctness or expressiveness, including:

- `lag`, `lead`, ranking, running totals, and framed windows;
- calendar generation with `sequence` and `explode`;
- row expansion and complex parsing;
- complex correlated rules or several tightly coupled calculations;
- cross joins and advanced set logic;
- state classification that is clearer as one documented query.

Do not split every expression into a separate operator. Keep a calculation together when it represents one business rule and is easier to test as a unit.

## Python and user-defined operators

Use Python only when built-ins and SQL are insufficient, for example:

- unsupported binary or specialist file processing;
- classical ML or specialist libraries;
- a one-off integration that cannot be expressed through a supported connector;
- custom output formatting.

Promote stable reusable logic to a user-defined operator when several Designer pipelines need it. Declare libraries in the serverless environment or governed dependency configuration; do not install packages during every run.

For external actions, prefer a separate Job task. If a Python or user-defined operator must perform the action, skip it during preview using `config["is_preview"]`, retrieve credentials from approved secret/connection mechanisms, use bounded retries, and record an idempotency key.

## Macros

| Macro type | Treatment |
|---|---|
| Standard macro | Inline a readable subgraph or replace stable reusable logic with a UDO |
| Batch macro | Prefer set-based SQL/Join processing; use a Job `For each` task only when iteration is intrinsic |
| Iterative macro | Redesign as set-based processing or orchestrate a bounded loop in Jobs |
| Analytic app/interface macro | Map controls to Job parameters or a Databricks App; do not invent fixed values |
| Connector macro | Replace with Lakeflow Connect, a UC connection, or a dedicated ingestion task |

Inventory referenced `.yxmc` files recursively. If a macro is missing, report it as a blocker rather than guessing its behavior.

## Reporting, predictive, and spatial tools

- Reporting tables/charts/layouts usually become a published table plus an AI/BI dashboard. Preserve required formatted files only when the consumer contract demands them.
- Email and Render are operational outputs, not ordinary transformations.
- Predictive tools require an explicit decision: preserve the trained artifact, retrain with MLflow tracking, or replace the model. Do not substitute a generative AI function for a classical model without approval.
- Spatial tools should use supported Databricks geospatial SQL/functions when available. Otherwise use a governed library or mark the step manual. Preserve coordinate reference systems and units.
- R tools require a reviewed reimplementation; do not perform a mechanical syntax translation.

## AI Functions

Use an AI Function only when the intended operation is semantic or generative, such as free-text classification, extraction, masking, translation, or summarization. First consider deterministic SQL, regex, and governed lookup tables. Evaluate cost, latency, privacy, non-determinism, and row cardinality. Persist and review mappings when repeatability matters.
