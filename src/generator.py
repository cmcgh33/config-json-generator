"""Compile fictional business configuration into a versioned JSON contract."""
import argparse
import json
import math
import re
from decimal import Decimal
from pathlib import Path


class ValidationError(ValueError):
    """A business configuration fails a required control."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def number(value, label):
    require(type(value) in (int, float) and math.isfinite(value),
            f"{label} must be a finite number")
    return Decimal(str(value))


def keys(value, expected, label):
    require(isinstance(value, dict), f"{label} must be an object")
    require(set(value) == set(expected), f"{label} requires exactly: {', '.join(expected)}")


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")


def generate(source):
    keys(source, ['model_id', 'model_name', 'factors'], 'input')
    text(source['model_id'], 'model_id')
    text(source['model_name'], 'model_name')
    require(re.fullmatch(r'[a-z][a-z0-9_]*', source['model_id']), 'model_id must use lowercase snake_case')
    factors = source['factors']
    require(isinstance(factors, list) and factors, 'factors must be a nonempty list')
    ids, total, compiled = set(), Decimal(0), []
    for i, factor in enumerate(factors):
        label = f'factors[{i}]'
        keys(factor, ['id', 'label', 'type', 'unit', 'weight_percent', 'rules'], label)
        text(factor['id'], label + '.id')
        require(re.fullmatch(r'[a-z][a-z0-9_]*', factor['id']), label + '.id must use lowercase snake_case')
        require(factor['id'] not in ids, label + '.id is duplicated')
        ids.add(factor['id'])
        text(factor['label'], label + '.label')
        text(factor['unit'], label + '.unit')
        weight = number(factor['weight_percent'], label + '.weight_percent')
        require(0 < weight <= 100, label + '.weight_percent must be > 0 and <= 100')
        total += weight
        require(factor['type'] in ('numeric', 'categorical'), label + '.type must be numeric or categorical')
        rules = factor['rules']
        require(isinstance(rules, list) and rules, label + '.rules must be a nonempty list')
        seen, previous_upper = set(), None
        for j, rule in enumerate(rules):
            location = f'{label}.rules[{j}]'
            expected = ['min', 'max', 'score'] if factor['type'] == 'numeric' else ['value', 'score']
            keys(rule, expected, location)
            score = number(rule['score'], location + '.score')
            require(0 <= score <= 100, location + '.score must be between 0 and 100')
            if factor['type'] == 'categorical':
                text(rule['value'], location + '.value')
                normalized = rule['value'].strip().casefold()
                require(normalized not in seen, location + '.value is duplicated')
                seen.add(normalized)
            else:
                lower, upper = rule['min'], rule['max']
                require(lower is None if j == 0 else lower is not None,
                        location + '.min must be null only for the first rule')
                require(upper is None if j == len(rules)-1 else upper is not None,
                        location + '.max must be null only for the last rule')
                lo = number(lower, location + '.min') if lower is not None else None
                hi = number(upper, location + '.max') if upper is not None else None
                require(lo is None or hi is None or lo < hi, location + ' has an empty or reversed range')
                require(j == 0 or lo == previous_upper, location + ' creates a gap or overlap')
                previous_upper = hi
        compiled.append({
            'id': factor['id'], 'label': factor['label'], 'type': factor['type'],
            'unit': factor['unit'], 'weight': float(weight / 100), 'rules': rules,
        })
    require(total == 100, f'weight_percent must total 100; got {total}')
    return {
        'schema_version': '1.0',
        'model': {'id': source['model_id'], 'name': source['model_name']},
        'scoring': {'range': [0, 100], 'higher_score': 'higher_risk',
                    'numeric_bounds': 'min_inclusive_max_exclusive'},
        'factors': compiled,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        source = json.loads(args.input.read_text(encoding='utf-8'))
        result = generate(source)
        payload = json.dumps(result, indent=2, allow_nan=False) + '\n'
        args.output.write_text(payload, encoding='utf-8')
    except (ValidationError, ValueError, OSError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(f'Generated {args.output} with {len(result["factors"])} validated factors')


if __name__ == '__main__':
    main()
