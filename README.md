# Config JSON Generator

Compile editable business configuration into consistent, validated JSON using Python.

Configuration teams often hand-maintain factors, weights, dropdown values, and score bands. Small errors such as overlapping ranges or weights that do not total 100% can make a configuration ambiguous. This project validates those controls before producing a versioned output contract.

## Try the live demo

[Open Config JSON Generator](https://carla-config-generator.streamlit.app/)

Click **Try fictional example** to explore the four-factor configuration immediately, or upload an edited Excel template and download the validated JSON. No local installation is needed to try the hosted demo.

## Run the interface locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed in your terminal. Click **Try fictional example** for a quick demo, or download the template, edit it in Excel, and upload the saved workbook. The interface validates inputs and output, previews the factors and rules, and enables JSON download after all checks pass.

See [the interface guide](docs/interface.md) for setup and a short demo walkthrough. The app is also hosted on Streamlit Community Cloud at the live demo link above.

## Command-line workflows

A Streamlit interface and command-line generator accepting JSON or Excel inputs, with four fictional commercial-credit factors, business validation, repeatable sample output, and automated tests. Python 3.10+. JSON generation uses no third-party dependencies; Excel import uses openpyxl and standalone output validation uses jsonschema.

```bash
python src/generator.py examples/sample_input.json examples/generated_config.json
```

For Excel input and the full test suite:

```bash
python -m pip install -r requirements.txt
python src/excel_importer.py examples/sample_input.xlsx examples/generated_config.json
python src/validate_config.py examples/generated_config.json
python -m unittest discover -s tests -v
```

Run the commands from the repository root. Edit `examples/sample_input.json` to change the model, weights, or rules, then regenerate the output. Invalid inputs produce an error and leave existing output unchanged. The output directory must already exist.

## Excel workflow

Download [the editable Excel template](examples/sample_input.xlsx). Change the amber input cells in **Model**, **Factors**, and **Rules**, save the workbook, then run the Excel command above. See [the workbook guide](docs/excel-template.md) for columns, boundary rules, and examples.

## Validate a received file

```bash
python src/validate_config.py examples/generated_config.json
```

This command reads the output without running the generator or modifying the file. It checks the versioned JSON Schema, then checks weight totals, unique IDs, categorical duplicates, and numeric range continuity. Errors identify the field, such as `$.factors[0].rules[1]`, and return exit code 1.

Generation and output validation are separate commands. Run both to demonstrate the complete workflow. See [the validation guide](docs/validation.md) for details and schema limitations.

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
| `app.py` | Upload, preview, validation errors, and download interface |
| `src/app_service.py` | In-memory workbook processing and output validation |
| `src/generator.py` | Validation and output compilation |
| `src/excel_importer.py` | Excel adapter reusing the same compiler |
| `examples/sample_input.xlsx` | Editable Excel template |
| `examples/sample_input.json` | Editable fictional business inputs |
| `examples/generated_config.json` | Reproducible output |
| `schemas/config_schema.json` | Version 1.0 output contract, JSON Schema Draft 2020-12 |
| `src/validate_config.py` | Standalone structure and business validation |
| `tests/` | Generator, Excel import, and output validation controls |
| `docs/requirements.md` | Scope, mappings, and acceptance criteria |
| `docs/architecture.md` | Design decisions and limitations |

## Roadmap

1. **Complete:** JSON input, Python compiler, validation, sample output, and tests.
2. **Complete:** Excel input template and import adapter.
3. **Complete:** Formal JSON Schema and independent output validation.
4. **Complete:** Interface for upload, error review, sample demo, and download.
5. **Complete:** Public demo hosting on Streamlit Community Cloud.
6. Portfolio walkthrough polish.

## Portfolio context

An independently designed personal project using fictional data and a custom format. All thresholds, scores, and weights are illustrative. No employer configuration, proprietary schemas, internal screenshots, or production data are included. This is an educational configuration tool, not a validated credit model.

Built by Carla McGhee with AI-assisted implementation. The documentation records the requirements and design decisions to make the work reviewable and explainable.
