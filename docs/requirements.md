# Requirements and data mapping

## User story

As a configuration analyst, I want to define weighted factors and scoring rules in a structured input, so that I can generate a consistent configuration without manually assembling the downstream JSON.

## MVP scope

One model per file. Numeric and categorical factors. Configurable weights and scores. A command-line workflow. Input can be JSON or the documented Excel template. Both paths share the same validation and output contract.

## Mapping

| Input | Output | Transformation |
| --- | --- | --- |
| `model_id` | `model.id` | Preserve validated snake_case identifier |
| `model_name` | `model.name` | Preserve nonempty display name |
| `factors[].weight_percent` | `factors[].weight` | Divide by 100 |
| Factor ID, label, type, unit, rules | Corresponding factor fields | Preserve after validation |
| None | `schema_version` | Set to `1.0` |
| None | `scoring` | Declare score range, direction, and boundary semantics |

## Acceptance criteria

- Valid four-factor example produces the committed output exactly.
- Weights totaling anything other than 100 are rejected.
- Each numeric factor covers the full numeric domain through adjacent bands; gaps, overlaps, reversed ranges, and misplaced open endpoints are rejected.
- Duplicate IDs and categorical values are rejected.
- Boolean, nonfinite, and string values cannot substitute for numbers.
- Scores outside 0–100 are rejected.
- Invalid input returns a nonzero exit code before writing output.
- Identical valid input produces identical JSON without timestamps or random identifiers.

## Assumptions

Higher scores represent higher risk. Units are explicit: LTV and debt yield use percentage points (75 means 75%); DSCR uses a ratio (1.4 means 1.4x). Numeric configuration bands deliberately cover all numbers, including negatives; a future observation-validation layer would enforce valid loan input domains. Categorical rules define a closed list; behavior for unknown observations belongs to a future evaluator.

## Success measurement

The MVP demonstrates predictable output and detection of invalid configurations through automated tests. No time savings or error-reduction percentages have been measured. A later user trial could compare manual assembly time and error counts against the generator.

## Excel acceptance criteria

- The sample workbook produces the same configuration values as sample JSON. Numeric spellings such as 1 and 1.0 may differ after Excel import, but have the same JSON numeric meaning.
- Sheet names and row 5 headers match the template contract.
- Unknown rule factor IDs and incompatible rule columns are rejected with cell locations.
- Blank numeric endpoints become null; numeric zero remains zero.
- Formula and error cells are rejected in importable inputs.
- Editing valid weights flows through to normalized output weights.
- New factors and rules can be appended through row 1005.

## Output contract acceptance criteria

- The version 1.0 schema conforms to JSON Schema Draft 2020-12.
- Both JSON-generated and Excel-generated configurations pass the standalone validator.
- Missing fields, unknown fields, incompatible rule structures, wrong versions, and incorrect scoring conventions fail structural validation.
- Normalized weights total 1 within an absolute tolerance of 1e-12 for floating-point serialization.
- Duplicate IDs/categories, gaps, overlaps, reversed ranges, and incorrect open endpoints fail business validation.
- The CLI rejects duplicate JSON keys and nonstandard numeric constants.
- Invalid output yields exit code 1 with field locations; valid output yields exit code 0.
- Validation never modifies the supplied file.

## Interface acceptance criteria

- The initial page offers an Excel template and a fictional example.
- Generation is disabled when no workbook is selected.
- Both sample and upload flows perform input compilation and independent output validation.
- Successful results show factor/rule counts, total weight, factor and rule previews, JSON text, and a JSON download.
- Invalid uploads display an error and no generated-file download.
- Changing or removing an upload clears previous results.
- A corrected upload can recover from an earlier failure.
- The service never writes uploaded files to disk and enforces documented file/archive limits.
