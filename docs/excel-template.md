# Excel input guide

## Generate a configuration

1. Download `examples/sample_input.xlsx` and open it in Excel.
2. Edit the amber input cells. Save as `.xlsx`.
3. Install the Excel reader once: `python -m pip install -r requirements.txt`.
4. From the repository root, run `python src/excel_importer.py examples/sample_input.xlsx examples/generated_config.json`.

Use your edited workbook path in the command if you saved another copy. Generation stops on invalid inputs. Existing output is left unchanged on validation failure.

## Workbook contract

Keep exactly three sheets named **Model**, **Factors**, and **Rules**. Keep row 5 headers unchanged. Do not add input columns. Enter literal values in imported cells; formulas and Excel errors are rejected. The formula on Model row 9 is informational and is not imported.

### Model

Enter `model_id` and `model_name` in row 6 only. Other rows are reserved for guidance and the total. The ID uses lowercase snake_case, for example `demo_cre_risk`.

### Factors

Data begins in row 6. Append records through row 1005. Blank rows are ignored.

| Column | Input |
| --- | --- |
| `id` | Unique lowercase snake_case ID |
| `label` | Display label |
| `type` | Dropdown: numeric or categorical |
| `unit` | Unit label, such as ratio, percent, category |
| `weight_percent` | Numeric percentage points; 40 means 40%, not 0.40 |

The Model total references Factors rows 6–1005 and highlights totals other than 100. This checks the total only; it does not establish that the workbook is valid. The importer checks all required controls.

### Rules

Data begins in row 6. Append records through row 1005. Each `factor_id` must match a Factors ID. Maintain the order of numeric bands for each factor, even if different factors' rules are interleaved.

| Column | Numeric factor | Categorical factor |
| --- | --- | --- |
| `factor_id` | Matching factor ID | Matching factor ID |
| `min` | Inclusive minimum; blank on first band | Leave blank |
| `max` | Exclusive maximum; blank on final band | Leave blank |
| `value` | Leave blank | Nonempty category name |
| `score` | Numeric value from 0 through 100 | Numeric value from 0 through 100 |

Leave unbounded endpoints empty; do not type the word `null`. Zero is a real numeric bound. At a shared boundary, the next band owns the value. Units use percentage points for LTV and debt yield (75 means 75%), and ratios for DSCR (1.4 means 1.4x).

## First experiment

Change DSCR weight from 40 to 35 and LTV weight from 30 to 35. The total stays 100, and generated weights become 0.35 and 0.35. Change only DSCR to 35 and generation fails because the total becomes 95.

## Adding a factor

Add a unique ID in Factors and one or more matching Rules rows, then rebalance all weights to 100. Changing a factor ID also requires changing its rule IDs. The importer rejects unknown rule IDs instead of discarding them.

## Verification

The committed workbook was rendered and reviewed on all three sheets. Its formula total was checked at 100, changed to 99 by editing one weight, and restored to 100 in the authoring engine. Automated tests verify that importing the exported workbook produces the same output as the JSON sample. Native Excel recalculation was not exercised in this environment.
