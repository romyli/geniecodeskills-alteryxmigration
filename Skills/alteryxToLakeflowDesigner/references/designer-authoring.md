# Lakeflow Designer authoring guidance

Use public Designer capabilities and current workspace behavior as the source of truth. Product capabilities change; check the current documentation or the target workspace when a feature is uncertain.

## Built-in surface

Designer currently documents these primary operators:

- Source, Enter Data, and Output;
- Aggregate, Combine, Unique, Filter, Guardrails, Join, Limit, Pivot, Sort, SQL, Select, Prepare, and Python;
- AI Function, Note, Group, and Visualization;
- user-defined operators for reusable custom behavior.

Prefer built-ins for common preparation because they are visible, governed, and easier for visual users to maintain. Use SQL for relational logic that is clearer or unavailable visually. Use Python for genuine library or integration needs.

## Readable graph design

- Give operators names that describe business purpose, not Alteryx tool numbers.
- Group related branches and add notes for assumptions and manual prerequisites.
- Keep source normalization near each source.
- Consolidate repeated metric branches into long-form rules where doing so preserves semantics.
- Materialize only useful boundaries; avoid persistence for every intermediate step.
- Preserve important business dimensions in published outputs.
- Use Guardrails for required columns, row counts, nullability, accepted values, ranges, regex checks, and key uniqueness where appropriate.

## Genie Code workflow

Provide Genie Code with a bounded task:

1. Attach or reference the Alteryx workflow and its inventory.
2. Name the exact UC sources and target.
3. Describe one logical branch or output at a time for complex workflows.
4. State null, case, duplicate, unmatched, and ordering requirements.
5. Ask it to add Guardrails and reconciliation queries.
6. Preview intermediate outputs, then run the full workflow.

Do not ask for a blind one-shot conversion of a large workflow. Review the proposed graph and source assumptions first.

## SQL and Python

For SQL operators, use explicit input names, deterministic ordering for windows, and named intermediate calculations. Avoid monolithic queries when separate business stages need independent validation; avoid artificial fragmentation when one rule is clearest as a single query.

For Python operators:

- assign the final DataFrame to `result`;
- use declared environment dependencies rather than runtime `pip install`;
- avoid driver collection for large datasets;
- guard side effects with `config["is_preview"]`;
- retrieve secrets from approved mechanisms;
- emit structured status/error data for external actions.

## User-defined operators

Use a UDO when custom behavior is stable, documented, and useful across multiple visual data preps. Keep one-off data logic in the current workflow unless central maintenance provides clear value. Test preview and full-run behavior separately.

## Exported `.designer.ipynb` files

Designer can export and import visual data prep files as `.designer.ipynb`. The notebook's internal cell serialization is not the preferred authoring API.

If raw artifact generation is explicitly required:

1. Export a minimal current artifact from the target workspace.
2. Treat it as the version-specific fixture.
3. Change only fields demonstrated by that export.
4. Do not assume template names, port names, or template versions from older samples.
5. Import the generated artifact into a non-production workspace path.
6. Verify every operator appears, opens, previews, and participates in Run all.
7. Keep source control diffs reviewable.

Samples in this repository are regression fixtures, not a stable serialization specification.

## Parameters and production

- Define visual data prep parameters for catalog, schema, environment, or other supported values.
- Store the file in a Databricks Git folder.
- Add it to a Lakeflow Job as a Visual data prep task when it depends on ingestion or feeds delivery tasks.
- Use Declarative Automation Bundles and environment targets for production deployment.
- Configure notifications and retry policy at the Job layer.

## Current documentation

- [Create a visual data prep](https://docs.databricks.com/aws/en/designer/build-transformation)
- [Built-in operators](https://docs.databricks.com/aws/en/designer/built-in-operators)
- [User-defined operators](https://docs.databricks.com/aws/en/designer/user-operators)
- [Move visual data prep to production](https://docs.databricks.com/aws/en/designer/production)
- [Extend Genie Code with skills](https://docs.databricks.com/aws/en/genie-code/skills)
