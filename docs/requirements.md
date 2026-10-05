# Requirements and data mapping

## User story

As a configuration analyst, I want to define weighted factors and scoring rules in a structured input, so that I can generate a consistent configuration without manually assembling the downstream JSON.

## MVP scope

One model per file. Numeric and categorical factors. Configurable weights and scores. A command-line workflow. Input is JSON for this milestone; Excel import is planned.

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
