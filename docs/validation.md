# Output validation

## Run the check

```bash
python -m pip install -r requirements.txt
python src/validate_config.py examples/generated_config.json
```

The command is independent of generation. It reads a completed JSON file and leaves it unchanged.

Success returns exit code 0. Invalid configurations return exit code 1 with field locations and reasons. For example, change the first factor's output weight from 0.4 to 0.39 and validation reports:

```text
Invalid configuration:
- $.factors: normalized weights must total 1; got 0.99
```

## Two validation layers

| Layer | Checks |
| --- | --- |
| JSON Schema | Required and allowed fields, data types, supported version, scoring conventions, nonempty labels, allowed rule structures, and numeric limits |
| Business validation | Weight total, unique IDs, normalized category uniqueness, band order, open endpoints, range direction, and continuity |

The schema is reusable by other Draft 2020-12 validators. Ordinary schema validation does not calculate a sum across factor weights or compare neighboring numeric bounds. Passing the schema alone does not establish business validity. The Python validator applies both layers.

The input parser also rejects duplicate object keys, `NaN`, and `Infinity`. In-memory and parsed overflow values must be finite. Structural errors are reported before business checks; once the structure passes, multiple business issues can be reported together.

## Numeric semantics

Output weights are fractions: 0.4 means 40%. The business validator sums decimal representations of those values and permits an absolute difference from 1 of at most 0.000000000001 (1e-12). This accommodates floating-point serialization; it is not intended to allow meaningful weight differences. Input weights still must total exactly 100 percentage points.

Numeric minimums are inclusive, maximums exclusive. Only the first minimum and last maximum may be null. A single unbounded band may have both endpoints null. Consecutive finite boundaries must match exactly; no tolerance is applied to rule boundaries. Higher scores mean higher risk throughout version 1.0.

## Versioning and portability

The contract is stored in `schemas/config_schema.json`; `$schema` declares Draft 2020-12 and the generated document's `schema_version` is `1.0`. The `$id` identifies the schema; the Python validator loads the local repository copy. All data references use local `$defs`, so checking a configuration does not fetch remote schemas.

A future incompatible field or semantic change should receive a new contract version and matching tests. The current validator intentionally rejects other versions.

These checks establish conformity to this project's configuration contract. Calibration, predictive performance, and downstream compatibility require separate work.

## Reference documentation

- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
- [Python jsonschema validation API](https://python-jsonschema.readthedocs.io/en/stable/validate/)
