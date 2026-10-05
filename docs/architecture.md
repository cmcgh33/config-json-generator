# Architecture and design decisions

The CLI reads a JSON file, validates business controls, compiles a versioned output object, and serializes it only after validation succeeds.

`generate(source)` is independent of file handling. A future Excel adapter or interface can reuse it without duplicating the validation rules. The function does not modify the supplied input.

Python's standard library keeps the first milestone easy to run. Decimal arithmetic checks weights exactly, avoiding binary floating-point summation errors. Output weights use ordinary JSON numbers. Serialization rejects nonfinite values, and fixed field order makes example changes easy to review.

Business validation is stricter than JSON parsing: syntactically valid input can still contain incorrect totals, duplicate values, or ambiguous ranges. A formal JSON Schema is planned to complement these cross-field checks.

## Boundaries and limitations

- Generates configuration; no borrower evaluation, grade assignment, calibration, or model performance claims.
- No Excel adapter, UI, formal JSON Schema, or third-party consumer integration yet.
- Validation reports the first failure; an interface could later collect multiple errors.
- Input size limits and concurrent writes are not implemented; this MVP is a local CLI.
- Validation failures leave existing output untouched. Output writes are not atomic against disk errors or interrupted execution.
- Changes to boundary semantics or field structure should increment the schema version and update examples and tests together.

## Interview walkthrough

Start with the manual configuration problem. Explain the input/output mapping, then demonstrate a successful generation. Change one weight to break the total and show the error. Explain why boundary ownership matters: without inclusive/exclusive conventions, one DSCR value could match two bands. Finish with the tests and the planned Excel adapter.
