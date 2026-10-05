"""Validate a generated configuration without running its generator."""
import argparse
from decimal import Decimal
import json
import math
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[1] / 'schemas/config_schema.json'
# The compiler serializes normalized weights as binary floating-point JSON numbers.
WEIGHT_TOLERANCE = Decimal('0.000000000001')


def location(parts):
    return '$' + ''.join(f'[{p}]' if isinstance(p, int) else f'.{p}' for p in parts)


def finite_errors(value, path=()):
    if isinstance(value, float) and not math.isfinite(value):
        return [f'{location(path)}: numbers must be finite']
    if isinstance(value, dict):
        return [error for key, item in value.items() for error in finite_errors(item, (*path, key))]
    if isinstance(value, list):
        return [error for i, item in enumerate(value) for error in finite_errors(item, (*path, i))]
    return []


def validate_config(config):
    """Return readable errors; an empty list means structure and business rules pass."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ValueError('Output validation requires: python -m pip install -r requirements.txt') from exc
    errors = finite_errors(config)
    if errors:
        return errors
    schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = [f'{location(error.absolute_path)}: {error.message}'
              for error in sorted(validator.iter_errors(config), key=lambda e: (location(e.absolute_path), e.message))]
    if errors:
        return errors
    factors = config['factors']
    total = sum((Decimal(str(f['weight'])) for f in factors), Decimal(0))
    if abs(total - 1) > WEIGHT_TOLERANCE:
        errors.append(f'$.factors: normalized weights must total 1; got {total}')
    ids = set()
    for i, factor in enumerate(factors):
        path = f'$.factors[{i}]'
        if factor['id'] in ids:
            errors.append(f'{path}.id: duplicate factor ID {factor["id"]!r}')
        ids.add(factor['id'])
        seen, previous_upper = set(), None
        rules = factor['rules']
        for j, rule in enumerate(rules):
            rule_path = f'{path}.rules[{j}]'
            if factor['type'] == 'categorical':
                key = rule['value'].strip().casefold()
                if key in seen:
                    errors.append(f'{rule_path}.value: duplicate categorical value')
                seen.add(key)
                continue
            lower, upper = rule['min'], rule['max']
            if (j == 0) != (lower is None):
                errors.append(f'{rule_path}.min: null is required only on the first band')
            if (j == len(rules)-1) != (upper is None):
                errors.append(f'{rule_path}.max: null is required only on the final band')
            lo = Decimal(str(lower)) if lower is not None else None
            hi = Decimal(str(upper)) if upper is not None else None
            if lo is not None and hi is not None and lo >= hi:
                errors.append(f'{rule_path}: empty or reversed numeric range')
            if j > 0 and (lo is None or previous_upper is None or lo != previous_upper):
                errors.append(f'{rule_path}: gap or overlap between numeric bands')
            previous_upper = hi
    return errors


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON object key: {key}')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f'Invalid JSON numeric constant: {value}')


def load_config(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      object_pairs_hook=unique_object, parse_constant=reject_constant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        errors = validate_config(load_config(args.input))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    if errors:
        parser.exit(1, 'Invalid configuration:\n' + '\n'.join(f'- {error}' for error in errors) + '\n')
    print(f'Valid configuration: {args.input} (schema 1.0; structure and business rules passed)')


if __name__ == '__main__':
    main()
