# Config JSON Generator

Compile editable business configuration into consistent, validated JSON using Python.

Configuration teams often hand-maintain factors, weights, dropdown values, and score bands. Small errors such as overlapping ranges or weights that do not total 100% can make a configuration ambiguous. This project validates those controls before producing a versioned output contract.

## Current milestone

A command-line generator with four fictional commercial-credit factors, business validation, repeatable sample output, and automated tests. Python 3.10+; no third-party dependencies.

```bash
python src/generator.py examples/sample_input.json examples/generated_config.json
python -m unittest discover -s tests -v
```

Run both commands from the repository root. Edit `examples/sample_input.json` to change the model, weights, or rules, then regenerate the output. Invalid inputs produce an error and leave existing output unchanged. The output directory must already exist.

## Example transformation

Input uses an analyst-friendly percentage:

```json
{"weight_percent": 40}
```

Output uses a normalized decimal:

```json
{"weight": 0.4}
```

The generator also adds schema version, score direction, and numeric boundary conventions. It creates configuration; it does not score borrowers or issue lending decisions.

## Validation controls

- Required fields and allowed types; unknown fields rejected.
- Unique lowercase factor IDs and positive weights totaling exactly 100%.
- Finite numeric values and scores between 0 and 100.
- Ordered numeric bands with no gaps or overlaps, covering the full numeric domain.
- Unique nonempty categorical values, ignoring case and surrounding spaces when checking duplicates.

Numeric bands include their minimum and exclude their maximum. `null` represents an unbounded endpoint. A value exactly at a shared boundary belongs to the next band. Input values and units must be interpreted by a downstream consumer; this compiler does not validate loan observations.

## Explore the project

| Path | Purpose |
| --- | --- |
| `src/generator.py` | Validation and output compilation |
| `examples/sample_input.json` | Editable fictional business inputs |
| `examples/generated_config.json` | Reproducible output |
| `tests/test_generator.py` | Business controls and failure behavior |
| `docs/requirements.md` | Scope, mappings, and acceptance criteria |
| `docs/architecture.md` | Design decisions and limitations |

## Roadmap

1. **Complete:** JSON input, Python compiler, validation, sample output, and tests.
2. Excel input template and import adapter.
3. Formal JSON Schema and independent output validation.
4. Simple interface for upload, error review, and download.

## Portfolio context

An independently designed personal project using fictional data and a custom format. All thresholds, scores, and weights are illustrative. No employer configuration, proprietary schemas, internal screenshots, or production data are included. This is an educational configuration tool, not a validated credit model.

Built by Carla McGhee with AI-assisted implementation. The documentation records the requirements and design decisions to make the work reviewable and explainable.
