import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.excel_importer import build_input, load_input, read_tables
from src.generator import generate, ValidationError

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'examples/sample_input.xlsx'


class ExcelImporterTests(unittest.TestCase):
    def setUp(self):
        self.tables = read_tables(TEMPLATE)

    def test_workbook_matches_json_input_and_output(self):
        source = json.loads((ROOT / 'examples/sample_input.json').read_text())
        expected = json.loads((ROOT / 'examples/generated_config.json').read_text())
        self.assertEqual(load_input(TEMPLATE), source)
        self.assertEqual(generate(load_input(TEMPLATE)), expected)

    def test_edited_weights_flow_to_output(self):
        self.tables['Factors'][0][1][4] = 35
        self.tables['Factors'][1][1][4] = 35
        result = generate(build_input(self.tables))
        self.assertEqual(result['factors'][0]['weight'], .35)
        self.assertEqual(result['factors'][1]['weight'], .35)

    def test_unknown_rule_id(self):
        self.tables['Rules'][0][1][0] = 'missing'
        with self.assertRaisesRegex(ValidationError, 'Rules!A6'):
            build_input(self.tables)

    def test_append_factor_and_rules(self):
        self.tables['Factors'][0][1][4] = 35
        self.tables['Factors'].append((10, ['demo_flag', 'Demo Flag', 'categorical', 'category', 5]))
        self.tables['Rules'].append((18, ['demo_flag', None, None, 'Yes', 25]))
        result = generate(build_input(self.tables))
        self.assertEqual(len(result['factors']), 5)
        self.assertEqual(result['factors'][-1]['weight'], .05)

    def test_duplicate_factor(self):
        self.tables['Factors'].append(copy.deepcopy(self.tables['Factors'][0]))
        with self.assertRaisesRegex(ValidationError, 'duplicate ID'):
            build_input(self.tables)

    def test_numeric_rule_with_category(self):
        self.tables['Rules'][0][1][3] = 'Office'
        with self.assertRaisesRegex(ValidationError, 'leave value blank'):
            build_input(self.tables)

    def test_category_with_numeric_bounds(self):
        self.tables['Rules'][-1][1][1] = 0
        with self.assertRaisesRegex(ValidationError, 'leave min/max blank'):
            build_input(self.tables)

    def test_zero_bound_preserved(self):
        self.tables['Rules'][0][1][2] = 0
        self.tables['Rules'][1][1][1] = 0
        self.assertEqual(build_input(self.tables)['factors'][0]['rules'][1]['min'], 0)
        generate(build_input(self.tables))

    def test_missing_score(self):
        self.tables['Rules'][0][1][4] = None
        with self.assertRaisesRegex(ValidationError, 'score must be a finite number'):
            generate(build_input(self.tables))

    def test_excel_structure_and_formula_rejected(self):
        # Test read-path controls with mocked workbook cells; never author via openpyxl.
        from openpyxl import load_workbook
        for defect in ('formula', 'header', 'extra_sheet'):
            wb = load_workbook(TEMPLATE)
            if defect == 'formula':
                wb['Factors']['E6'] = '=20+20'
            elif defect == 'header':
                wb['Factors']['E5'] = 'wrong'
            else:
                wb.create_sheet('Extra')
            with patch('openpyxl.load_workbook', return_value=wb):
                with self.assertRaises(ValidationError):
                    read_tables(TEMPLATE)
            wb.close()

    def test_cli_success(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            run = subprocess.run([sys.executable, str(ROOT/'src/excel_importer.py'), str(TEMPLATE), str(output)], capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(output.read_text()), generate(load_input(TEMPLATE)))

    def test_bad_workbook_leaves_output_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/'bad.xlsx', Path(directory)/'result.json'
            source.write_text('not a workbook')
            output.write_text('keep')
            run = subprocess.run([sys.executable, str(ROOT/'src/excel_importer.py'), str(source), str(output)], capture_output=True)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(output.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
