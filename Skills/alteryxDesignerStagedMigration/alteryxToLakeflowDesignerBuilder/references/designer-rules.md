# Lakeflow Designer build rules

## Sources

Use only source contracts approved in the plan. Use Source for UC tables, views, governed
Volume files, or approved onboarding targets. Do not point Databricks at inaccessible UNC or
local paths and do not fabricate Enter Data rows for external dependencies.

## Core semantic invariants

- Preserve Filter included/excluded anchors when consumed.
- Preserve Join type, keys, comparison normalization, multiplicity, unmatched anchors,
  selected/dropped fields, aliases, types, and ordering.
- Preserve Union by-name/by-position behavior, missing-column handling, and duplicate policy.
- Preserve Unique survivor ordering when it matters.
- Preserve Formula sequence, null/empty behavior, and data types.
- Account for zero-based Alteryx `FindString` versus one-based Spark `locate`.
- Match date/timestamp boundaries and timezone assumptions; do not introduce `CAST(... AS DATE)`
  merely to simplify a timestamp predicate.
- Define partition, ordering, and frames for Multi-Row and running calculations.
- Treat Dynamic Rename and data-dependent schemas as explicit manual or SQL design decisions.

## Visual graph

Prefer supported visual operators when they clearly express behavior. Use Notes for changed
source/output contracts and deferred operational tasks, Groups for business branches, and
Guardrails for meaningful schema, null, accepted-value, row-count, and key checks. A smaller
graph is valuable only when equivalence is documented and testable.

## Outputs and side effects

Choose tables, materialized views, or governed Volume files from the approved consumer
contract. Record original file format, encoding, header, BOM, naming, and delivery obligations
when replacing an external file. Keep email, HTTP, commands, rendering, network delivery,
previous-run state, and ordering of side effects in Lakeflow Jobs or explicit manual work.

## Structural validation

Reject a build with missing active branches, unintended output columns, unresolved source
stand-ins, unmapped workflow Events, undocumented semantic changes, or plan hash mismatch.
Opening an artifact proves only import compatibility; preview, full run, and reconciliation
remain separate stages.
