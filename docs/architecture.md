# Architecture and design decisions

The CLI reads a JSON file, validates business controls, compiles a versioned output object, and serializes it only after validation succeeds.

`generate(source)` is independent of file handling. The Excel adapter and a future interface reuse it without duplicating the validation rules. The function does not modify the supplied input.

Python's standard library keeps the first milestone easy to run. Decimal arithmetic checks weights exactly, avoiding binary floating-point summation errors. Output weights use ordinary JSON numbers. Serialization rejects nonfinite values, and fixed field order makes example changes easy to review.

Business validation is stricter than JSON parsing: syntactically valid input can still contain incorrect totals, duplicate values, or ambiguous ranges. A formal JSON Schema is planned to complement these cross-field checks.

## Boundaries and limitations

- Generates configuration; no borrower evaluation, grade assignment, calibration, or model performance claims.
- Excel import uses openpyxl only to read workbook inputs; the compiler stays independent of that dependency.
- No UI, formal JSON Schema, or third-party consumer integration yet.
- The workbook total is a convenience check; the compiler remains authoritative for all business controls.
- Excel input supports 1,000 data rows per table, literal cells only, and the three documented sheets.
- Validation reports the first failure; an interface could later collect multiple errors.
- Input size limits and concurrent writes are not implemented; this MVP is a local CLI.
- Validation failures leave existing output untouched. Output writes are not atomic against disk errors or interrupted execution.
- Changes to boundary semantics or field structure should increment the schema version and update examples and tests together.

## Interview walkthrough

Start with the manual configuration problem. Explain the input/output mapping, then demonstrate a successful generation. Change one weight to break the total and show the error. Explain why boundary ownership matters: without inclusive/exclusive conventions, one DSCR value could match two bands. Finish with the tests and the planned Excel adapter.
