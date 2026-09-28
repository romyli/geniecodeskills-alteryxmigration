# Staged migration workflow

Use this process for POCs and production migrations where a one-shot conversion would hide
source assumptions or semantic drift. Keep the human gates focused on decisions that change
the result; routine visual operator construction does not require individual approval.

## Stage 1: assess

Produce:

- effective active/inactive node and connection counts;
- referenced macro resolution, including missing paths;
- source-readiness and output-contract matrices;
- external actions and workflow-level Events;
- semantic hotspots such as Join projections, windows, state, dynamic schemas, and side effects;
- a recommended build decomposition by output or logical branch.

Gate 1 requires the user to approve or supply source onboarding, target outputs, unresolved
macros, and operational ownership. Stop here when any of these decisions would materially
change the graph.

## Stage 2: design

Produce:

- the four target layers: ingestion, Designer transformation, published outputs, and Jobs;
- a mapping ledger for every effectively enabled Alteryx node or consolidated pattern;
- the intended Designer graph grouped by business branch;
- explicit rationales for consolidation or changed source/output contracts;
- expected schemas and validation checks at branch and output boundaries.

Gate 2 requires approval of the graph, semantic changes, and manual boundaries. Do not create
an artifact merely to make unresolved design choices concrete.

## Stage 3: build approved scope

Build only the approved output or branch set. For each branch:

1. Add approved Sources and normalize them near ingestion.
2. Implement transformations without synthetic stand-ins for missing data.
3. Add Guardrails at meaningful contracts.
4. Preview intermediate outputs when data is available.
5. Run structural parity before moving to the next branch.

For a small, low-risk workflow, the user may approve all branches in one build. For larger or
riskier workflows, checkpoint by output or shared foundation. Stop when an unavailable source
or ambiguous rule prevents faithful implementation.

## Stage 4: validate

Run structural checks first, then reconciliation on comparable snapshots. Structural checks
must reject missing active branches, unintended output columns, unresolved placeholders,
unmapped Events, and consolidations without an equivalence rationale. Data validation covers
schema, population, values, business boundaries, and operational behavior.

Gate 3 is owner acceptance of explained differences. A generated or imported artifact is not
validated merely because it opens.

## Stage 5: productionize

Parameterize environments, create Job dependencies and delivery tasks, configure retries and
notifications, and define deployment and rollback. Enabling schedules, external delivery,
APIs, or messages requires explicit approval at the point of activation.

## Risk-based decomposition

Use fewer gates when sources are ready, transformations are deterministic, there are no
side effects, and the graph has one clear output. Split by output or shared foundation when
there are multiple source families, joins with non-unique keys, windows, dynamic schemas, or
several consumer contracts. Treat missing macros, proprietary formats, previous-run state,
HTTP/email actions, and very large graphs as separate workstreams rather than canvas details.

## Continuation handoff

At every stop, report:

- skill revision and completed mode;
- approved and unresolved decisions;
- artifacts produced or modified;
- highest validation stage reached;
- the exact next mode and scope to request.

When continuing in a new chat, attach or reference the inventory and approved design so the
next run does not rediscover or reinterpret decisions. After updating an installed skill,
start a fresh chat or explicitly reload it before continuing.
