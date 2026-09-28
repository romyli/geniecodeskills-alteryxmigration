# alteryx-to-lakeflow-designer — Sample Workflows

End-to-end conversion examples for the `alteryx-to-lakeflow-designer` skill. Each sample
contains the **source Alteryx workflow** (`.yxmd`) and the **resulting
Lakeflow Designer Visual Data Prep pipeline** (`.designer.ipynb`) that the
skill produced from it.

| Sample | Tools exercised | Source | Target |
|---|---|---|---|
| [`RetailAnalyticsComplex`](./RetailAnalyticsComplex) | Input Data, Filter, DateTime, Formula, RegEx, Text-to-Columns, Multi-Field Formula, Join, Find Replace, Imputation, Append Fields, Sort, Multi-Row Formula, Unique, Tile, Running Total, Summarize, Cross Tab, Transpose, Generate Rows, Union, Sample, Select, Text Input, Output Data | `RetailAnalyticsComplex.yxmd` | `RetailAnalyticsComplex.designer.ipynb` |
| [`RetailAnalyticsAdvancedML`](./RetailAnalyticsAdvancedML) | Everything above *plus* Record ID, Auto Field, Data Cleansing, Fuzzy Match, Make Group, Create Points, Buffer, Find Nearest, Spatial Match, Count Records, Weighted Average, Random %Sample, Oversample Field, Create Samples, Linear Regression, Score, TS Plot, ARIMA Forecast, Cache, Test, Message, Block Until Done, Tool Container, Comment, Macro reference | `RetailAnalyticsAdvancedML.yxmd` | `RetailAnalyticsAdvancedML.designer.ipynb` |

Both Alteryx workflows operate on the same synthetic retail dataset
(20,000,000 transaction rows + small product / store dims) hosted in Unity
Catalog at `aldi_aus.demo.raw_test`:

| File | Rows | Purpose |
|---|---|---|
| `transactions.csv` | 20,000,000 | Sale-line records with deliberate quality issues (nulls, dupes, mixed-case fields, regex-parseable codes) |
| `product_catalog.csv` | 5,000 | Product dim with `^[A-Z]{2,4}-\d{3,5}-[A-Z0-9]{2,4}$` codes |
| `stores.csv` | 250 | Store dim across 8 AU regions |

## Why these samples?

Together the two `.yxmd` files exercise a broad selection of Alteryx tools.
Use them as regression fixtures when iterating on the skill. The generated
`.designer.ipynb` files reflect the Designer export format at the time they
were created; they are examples, not a stable serialization specification.

## Re-running the conversion

From a Databricks workspace with this skill installed:

```
@alteryx-to-lakeflow-designer convert ./Samples/RetailAnalyticsComplex/RetailAnalyticsComplex.yxmd
@alteryx-to-lakeflow-designer convert ./Samples/RetailAnalyticsAdvancedML/RetailAnalyticsAdvancedML.yxmd
```

The skill expects the source CSVs to be available at
`/Volumes/aldi_aus/demo/raw_test/`. Adjust the source paths inside each
`.yxmd` if you regenerate the dataset somewhere else.
