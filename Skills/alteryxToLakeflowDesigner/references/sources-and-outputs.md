# Sources, outputs, and operational boundaries

Read this reference whenever an Alteryx workflow touches anything outside existing Unity Catalog data.

## Source-readiness matrix

| Source | Recommended onboarding | Key caveats |
|---|---|---|
| Unity Catalog table/view | Designer Source | Confirm grants, schema, freshness, and environment |
| UC Volume files | Designer Source or ingestion pipeline | Prefer stable folders and explicit schemas for recurring loads |
| Local CSV/Excel | Upload/create table for a POC; automate landing for production | Capture sheet, range, header, encoding, and filename semantics |
| Cloud object storage | Auto Loader/Lakeflow ingestion into bronze, then Designer | Use UC external locations/Volumes and managed identities |
| SharePoint Online files | Managed Lakeflow Connect SharePoint connector | Uses OAuth; supports incremental ingestion and schema evolution |
| SharePoint Online lists | Managed Lakeflow Connect SharePoint list ingestion | Validate list types, deleted items, attachments, and lookup columns |
| Legacy/on-prem SharePoint | Usually a separate edge extraction or migration to SharePoint Online | Legacy basic authentication such as SharePoint 2007 is not a drop-in fit for the managed OAuth connector |
| SFTP | Standard Lakeflow Connect SFTP/Auto Loader connector | Requires network reachability and UC connection; no write-back to SFTP |
| SMB/UNC network share | Scheduled transfer to cloud storage, SharePoint Online, or a UC Volume | Databricks compute normally cannot read a corporate Windows share directly |
| Exasol or another database | Approved replication, JDBC ingestion, or federation when supported | Land stable bronze tables before Designer where possible |
| API | Dedicated ingestion task or managed connector | Store checkpoints, rate-limit, and make retries idempotent |
| Alteryx YXDB | One-time Alteryx export to Parquet/CSV, then Delta | Proprietary; do not rely on unverified reverse-engineering libraries |

Lakeflow Connect normally creates governed Delta streaming tables. Use those tables as Designer Sources rather than mixing connector logic into the transformation canvas.

## Recurring file patterns

Replace manually enumerated monthly file inputs with a governed landing convention:

1. Land files under a stable folder such as `/Volumes/<catalog>/<schema>/<volume>/<feed>/`.
2. Preserve source metadata such as filename and ingestion timestamp.
3. Ingest incrementally into a bronze table when files arrive repeatedly.
4. Apply schema checks and quarantine malformed files.
5. Point Designer at the bronze table.

Do not infer period solely from a hard-coded filename when the file contains an authoritative business date.

## Outputs

Designer Output supports managed Unity Catalog tables, materialized views, and CSV/Excel/JSON files in UC Volumes. Choose the output from the consumer contract:

- **Table**: default for reusable governed datasets and Tableau/BI consumption.
- **Materialized view**: use when refresh semantics and query shape fit the feature.
- **Volume file**: use when a downstream consumer genuinely requires a file.

Delta is preferred as a governed system of record, but do not force an extra table when the user has intentionally requested a transient file-only artifact and governance requirements permit it.

### Proprietary and network outputs

- Replace Tableau Hyper generation with a UC table and the Databricks Tableau connector when consumers can migrate.
- Replace YXDB output with Delta or Parquet.
- Write files to a UC Volume, then use a separate delivery task if they must reach SMB, SFTP, or another external system.
- SFTP ingestion does not imply SFTP write-back support.

## Append, overwrite, and state

Do not copy the Alteryx output mode blindly:

- Use overwrite for complete reproducible snapshots.
- Use append only when duplicate prevention and replay behavior are defined.
- Use merge/upsert when keys and update semantics are explicit.
- Replace “previous runs” Excel files with a Delta state table and a stable business/idempotency key.

## APIs, email, and external delivery

Keep operational actions downstream of successful data publication:

```text
ingestion → Designer transformation → validated Delta output → delivery/API/email task
```

For every side effect specify:

- trigger condition and upstream dependency;
- idempotency key and durable delivery status;
- authentication mechanism;
- timeout, bounded retry, and failure path;
- whether partial success is possible;
- safe replay behavior;
- preview behavior.

Job notifications are appropriate for static operational alerts. They are not automatically equivalent to an Alteryx email that builds dynamic recipients, attachments, or message bodies from data.

## Security review

Alteryx XML can contain usernames, encrypted password material, connection identifiers, email addresses, internal URLs, and query text. During migration:

- report secret material without echoing its value;
- rotate credentials when repository exposure or unknown encryption scope makes that prudent;
- prefer OAuth/service principals and least-privilege read identities;
- store connection configuration in Unity Catalog connections;
- store remaining secrets in an approved secret mechanism;
- avoid placing sensitive endpoint or recipient data in skill prompts and examples;
- retain source-system access controls when publishing target tables.

## Current documentation

- [Lakeflow Connect file connectors](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/file-connectors-overview)
- [Managed SharePoint connector](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sharepoint)
- [SFTP ingestion](https://docs.databricks.com/aws/en/ingestion/sftp)
- [Designer ingestion](https://docs.databricks.com/aws/en/designer/ingest-data)
