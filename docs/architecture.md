# Architecture and design decisions

The CLI reads a JSON file, validates business controls, compiles a versioned output object, and serializes it only after validation succeeds.

`generate(source)` is independent of file handling. The Excel adapter and a future interface reuse it without duplicating the validation rules. The function does not modify the supplied input.

Python's standard library keeps the first milestone easy to run. Decimal arithmetic checks weights exactly, avoiding binary floating-point summation errors. Output weights use ordinary JSON numbers. Serialization rejects nonfinite values, and fixed field order makes example changes easy to review.

Business validation is stricter than JSON parsing: syntactically valid input can still contain incorrect totals, duplicate values, or ambiguous ranges. The output schema in `schemas/config_schema.json` complements cross-field checks. The standalone validator reads a generated file, applies Draft 2020-12 schema validation with jsonschema, then independently checks totals, duplicates, and numeric band continuity. It does not call the generator, repair the file, or import openpyxl.

## Boundaries and limitations

- Generates configuration; no borrower evaluation, grade assignment, calibration, or model performance claims.
- Excel import uses openpyxl only to read workbook inputs; the compiler stays independent of that dependency.
- The Streamlit interface calls an in-memory workbook service, then displays only validated results.
- The public demo is hosted at https://carla-config-generator.streamlit.app/ on Streamlit Community Cloud. No third-party consumer integration is implemented.
- The workbook total is a convenience check; the compiler remains authoritative for all business controls.
- Excel input supports 1,000 data rows per table, literal cells only, and the three documented sheets.
- Input compilation reports the first failure. Output validation reports multiple structural errors, or multiple business errors once the structure passes.
- The interface limits uploaded files to 5 MB, expanded workbook archives to 20 MB, and archive entries to 300. These limits apply to the interface service; CLI commands retain their original local-file behavior.
- Uploaded workbook bytes and generated output stay in process memory; the application does not write uploads to files. Changing or clearing an upload clears the previous result.
- Session state holds each visitor's current generated result. There is no application database, shared upload cache, or authentication.
- Validation failures leave existing output untouched. Output writes are not atomic against disk errors or interrupted execution.
- Changes to boundary semantics or field structure should increment the schema version and update examples and tests together.

## Interview walkthrough

Start with the manual configuration problem. Explain the input/output mapping, then demonstrate a successful generation. Change one weight to break the total and show the error. Explain why boundary ownership matters: without inclusive/exclusive conventions, one DSCR value could match two bands. Run the independent output validator, then finish with the tests and Excel adapter.
