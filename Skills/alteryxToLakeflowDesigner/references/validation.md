# Migration validation

Validation compares equivalent business states. Do not compare a current Databricks run with a historical Alteryx output produced from different source data and treat the difference as a transformation defect.

## Establish the baseline

Prefer this order:

1. Freeze representative source inputs and capture the corresponding Alteryx outputs.
2. Run Alteryx and Designer against equivalent snapshots during a parallel-run window.
3. If expected output is unavailable, agree on invariants and create reviewed test fixtures from representative cases.

Expected output is strongly preferred, but its absence need not block inventory, design, or an initial implementation.

## Reconciliation layers

### 1. Schema

Compare:

- column names and order where consumers depend on order;
- data types, precision, scale, and nullability;
- renamed and dropped fields;
- generated columns and metadata fields.

Use `DECIMAL(p,s)` for Alteryx FixedDecimal behavior when financial or regulated calculations require it. Do not assume floating-point differences are harmless.

### 2. Population

Compare:

- total row count;
- counts by important business dimensions and dates;
- Filter included/excluded branch counts;
- Join matched/left-unmatched/right-unmatched counts;
- duplicate and unique-key counts;
- null counts and accepted-value distributions.

### 3. Values

When stable keys exist, perform row-level comparison for:

- missing and extra keys;
- changed categorical values;
- absolute and relative numeric differences;
- date/timestamp and timezone differences;
- case, whitespace, and empty-string/null differences.

When stable keys do not exist, compare deterministic hashes over an agreed sorted column set plus aggregate checks.

### 4. Business rules

Test representative boundary conditions explicitly:

- first/last row in window calculations;
- dates at month/year boundaries and daylight-saving changes;
- unmatched and duplicate join keys;
- zero denominators, nulls, and invalid numeric strings;
- threshold boundaries and exception routing;
- replay of already-processed files or notifications.

### 5. Operational behavior

Validate scheduling, retries, partial failures, append/merge behavior, late-arriving data, file naming, external delivery, and alerting. A matching table is insufficient if the workflow sends duplicate notifications or loses state on retry.

## Tolerances

Do not use universal thresholds such as “within 0.1%.” Define tolerance per metric from business meaning and source data types:

- exact for identifiers, counts, statuses, and deterministic decimal calculations;
- approved rounding tolerance for measures intentionally rounded at different stages;
- statistical acceptance criteria only for intentionally non-deterministic algorithms.

Document the owner and rationale for every non-zero tolerance.

## Validation output

Produce a compact report containing:

- baseline identity and run timestamps;
- source snapshot identifiers;
- passed/failed schema and population checks;
- largest material differences with example keys;
- manual or operational tests still outstanding;
- disposition: pass, pass with accepted differences, or fail.

Retain useful reconciliation queries, Guardrails, or test tables for regression testing. Remove only temporary artifacts that have no ongoing value.

## Cutover

Before cutover:

- complete at least one representative parallel run;
- obtain owner acceptance for explained differences;
- confirm consumer connectivity and output contract;
- verify rollback or rerun procedure;
- disable the Alteryx schedule only after the Databricks run and delivery path are proven.
