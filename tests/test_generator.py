import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.generator import generate, ValidationError

ROOT = Path(__file__).resolve().parents[1]


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((ROOT / 'examples/sample_input.json').read_text())

    def test_example_matches_committed_output(self):
        expected = json.loads((ROOT / 'examples/generated_config.json').read_text())
        self.assertEqual(generate(self.source), expected)
        self.assertEqual(generate(copy.deepcopy(self.source)), expected)

    def reject(self, mutate):
        mutate(self.source)
        with self.assertRaises(ValidationError):
            generate(self.source)

    def test_invalid_weights(self):
        self.reject(lambda s: s['factors'][0].update(weight_percent=39))

    def test_overlapping_bands(self):
        self.reject(lambda s: s['factors'][0]['rules'][1].update(min=0.9))

    def test_gap_in_bands(self):
        self.reject(lambda s: s['factors'][0]['rules'][1].update(min=1.1))

    def test_missing_open_bound(self):
        self.reject(lambda s: s['factors'][0]['rules'][0].update(min=0))

    def test_duplicate_categories(self):
        self.reject(lambda s: s['factors'][-1]['rules'][1].update(value=' OFFICE '))

    def test_duplicate_factor_ids(self):
        self.reject(lambda s: s['factors'][1].update(id='dscr'))

    def test_boolean_and_nonfinite_numbers(self):
        for value in (True, float('nan'), float('inf'), '40'):
            source = copy.deepcopy(self.source)
            source['factors'][0]['weight_percent'] = value
            with self.assertRaises(ValidationError):
                generate(source)

    def test_out_of_range_score(self):
        self.reject(lambda s: s['factors'][0]['rules'][0].update(score=101))

    def test_unknown_fields(self):
        self.reject(lambda s: s.update(unrecognized=True))

    def test_invalid_input_does_not_overwrite_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'input.json', Path(directory) / 'output.json'
            source.write_text('{"bad": true}')
            output.write_text('keep existing output')
            run = subprocess.run([sys.executable, str(ROOT / 'src/generator.py'), str(source), str(output)], capture_output=True)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(output.read_text(), 'keep existing output')


if __name__ == '__main__':
    unittest.main()
