# Planning notebook

Create a conventional Databricks/Jupyter notebook for human review. It is not a Lakeflow
Designer `.designer.ipynb` export and must not contain the migrated transformation.

## Required sections

1. **Provenance** — planner revision, plan schema version, workflow paths and SHA-256 hashes.
2. **Executive summary** — complexity, proposed decomposition, and blocking decisions.
3. **Active graph inventory** — active/inactive counts, macros, branches, and outputs.
4. **Source readiness** — original source, classification, proposed target, owner, and status.
5. **Output and operations** — consumer contracts, Events, APIs, delivery, and state.
6. **Target design** — ingestion, Designer, outputs, and Jobs.
7. **Mapping ledger** — Alteryx nodes/patterns to target behavior and consolidation rationale.
8. **Expected schemas** — important intermediate and published columns, types, and keys.
9. **Validation plan** — structural, data, boundary, and operational checks.
10. **Decision register** — proposed, approved, rejected, and unresolved decisions.
11. **Approval gate** — exact questions the human must answer before building.

## Executable cells

Executable cells are optional and read-only. Use them only to profile approved UC data:

- schema and nullability;
- row and duplicate-key counts;
- Join key cardinality and unmatched populations;
- accepted values and date ranges;
- representative boundary cases.

Do not write tables or files, install packages, mutate source state, invoke APIs, send
notifications, or execute copied Alteryx queries against a live system without explicit
authorization. Keep derived profiling results compact and avoid displaying secrets or
personal recipient details.

## Consistency

The YAML plan is the machine contract. The notebook may explain it but must not introduce a
source mapping, branch decision, or approved change absent from YAML. Regenerate or update
both artifacts when the plan changes.
