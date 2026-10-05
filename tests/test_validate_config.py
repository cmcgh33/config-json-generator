import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator
from src.excel_importer import load_input
from src.generator import generate
from src.validate_config import load_config, SCHEMA_PATH, validate_config

ROOT = Path(__file__).resolve().parents[1]


class OutputValidationTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / 'examples/generated_config.json')

    def reject(self, mutate, expected):
        mutate(self.config)
        errors = validate_config(self.config)
        self.assertTrue(errors)
        self.assertTrue(any(expected in error for error in errors), errors)

    def test_schema_is_valid_and_accepts_sample(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        Draft202012Validator.check_schema(schema)
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(self.config)), [])
        self.assertEqual(validate_config(self.config), [])

    def test_both_generation_paths_pass(self):
        source = load_config(ROOT / 'examples/sample_input.json')
        self.assertEqual(validate_config(generate(source)), [])
        self.assertEqual(validate_config(generate(load_input(ROOT / 'examples/sample_input.xlsx'))), [])

    def test_missing_required_field(self):
        self.reject(lambda c: c.pop('model'), 'required property')

    def test_unknown_field(self):
        self.reject(lambda c: c.update(surprise=True), 'Additional properties')

    def test_wrong_version(self):
        self.reject(lambda c: c.update(schema_version='2.0'), '$.schema_version')

    def test_wrong_scoring_direction(self):
        self.reject(lambda c: c['scoring'].update(higher_score='lower_risk'), '$.scoring.higher_score')

    def test_wrong_boundary_semantics(self):
        self.reject(lambda c: c['scoring'].update(numeric_bounds='inclusive_both'), '$.scoring.numeric_bounds')

    def test_boolean_score(self):
        self.reject(lambda c: c['factors'][0]['rules'][0].update(score=True), '.score')

    def test_string_weight(self):
        self.reject(lambda c: c['factors'][0].update(weight='0.4'), '.weight')

    def test_empty_label(self):
        self.reject(lambda c: c['factors'][0].update(label='  '), '.label')

    def test_out_of_range_score(self):
        self.reject(lambda c: c['factors'][0]['rules'][0].update(score=101), '.score')

    def test_numeric_factor_with_categorical_rule(self):
        self.reject(lambda c: c['factors'][0].update(rules=[{'value':'Office','score':20}]), '.rules[0]')

    def test_duplicate_ids(self):
        self.reject(lambda c: c['factors'][1].update(id='dscr'), 'duplicate factor ID')

    def test_wrong_total_schema_alone_does_not_catch(self):
        self.config['factors'][0]['weight'] = .39
        schema = json.loads(SCHEMA_PATH.read_text())
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(self.config)), [])
        self.assertTrue(any('must total 1' in e for e in validate_config(self.config)))

    def test_float_serialization_tolerance(self):
        for factor, weight in zip(self.config['factors'], [.1,.2,.3,.4000000000000001]):
            factor['weight'] = weight
        self.assertEqual(validate_config(self.config), [])
        self.config['factors'][-1]['weight'] = .400001
        self.assertTrue(any('must total 1' in e for e in validate_config(self.config)))

    def test_overlapping_ranges(self):
        self.reject(lambda c: c['factors'][0]['rules'][1].update(min=.9), 'gap or overlap')

    def test_gap_in_ranges(self):
        self.reject(lambda c: c['factors'][0]['rules'][1].update(min=1.1), 'gap or overlap')

    def test_reversed_range(self):
        self.reject(lambda c: c['factors'][0]['rules'][1].update(max=.5), 'empty or reversed')

    def test_missing_unbounded_endpoint(self):
        self.reject(lambda c: c['factors'][0]['rules'][0].update(min=0), '.min')

    def test_duplicate_category_values(self):
        self.reject(lambda c: c['factors'][-1]['rules'][1].update(value=' OFFICE '), 'duplicate categorical')

    def test_nonfinite_numbers(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            config = copy.deepcopy(self.config)
            config['factors'][0]['weight'] = value
            self.assertTrue(any('finite' in error for error in validate_config(config)))

    def test_reject_duplicate_json_keys_and_constants(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            for payload in ('{"schema_version":"1.0","schema_version":"2.0"}', '{"weight":NaN}', '{"weight":Infinity}'):
                path.write_text(payload)
                with self.assertRaises(ValueError):
                    load_config(path)

    def test_collect_multiple_business_errors(self):
        self.config['factors'][0]['weight'] = .39
        self.config['factors'][0]['rules'][1]['min'] = .9
        errors = validate_config(self.config)
        self.assertTrue(any('must total 1' in error for error in errors))
        self.assertTrue(any('gap or overlap' in error for error in errors))

    def test_cli_exit_codes_and_file_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'config.json'
            for valid in (True, False):
                config = copy.deepcopy(self.config)
                if not valid:
                    config['factors'][0]['weight'] = .39
                payload = json.dumps(config)
                path.write_text(payload)
                run = subprocess.run([sys.executable,str(ROOT/'src/validate_config.py'),str(path)],capture_output=True,text=True)
                self.assertEqual(run.returncode, 0 if valid else 1, run.stderr)
                self.assertEqual(path.read_text(), payload)
                if not valid:
                    self.assertIn('$.factors', run.stderr)


if __name__ == '__main__':
    unittest.main()
