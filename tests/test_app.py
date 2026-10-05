from io import BytesIO
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

from streamlit.testing.v1 import AppTest
from src.app_service import compile_workbook, WorkbookError, MAX_UPLOAD_BYTES
from src.validate_config import validate_config

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT/'examples/sample_input.xlsx').read_bytes()
MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class WorkbookServiceTests(unittest.TestCase):
    def test_download_payload_is_valid_configuration(self):
        result = compile_workbook(TEMPLATE)
        self.assertEqual(json.loads(result['payload']), result['config'])
        self.assertEqual(validate_config(result['config']), [])
        self.assertEqual(result['filename'], 'demo_cre_risk_config.json')

    def test_bad_and_empty_uploads(self):
        for content in (b'', b'not an Excel file', b'PK broken zip'):
            with self.assertRaises(WorkbookError):
                compile_workbook(content)

    def test_upload_size_limit(self):
        with self.assertRaisesRegex(WorkbookError, '5 MB'):
            compile_workbook(b'0' * (MAX_UPLOAD_BYTES + 1))

    def test_non_workbook_zip(self):
        buffer = BytesIO()
        with ZipFile(buffer, 'w') as archive:
            archive.writestr('ordinary.txt', 'hello')
        with self.assertRaisesRegex(WorkbookError, 'not an Excel workbook'):
            compile_workbook(buffer.getvalue())

    def test_malformed_workbook_xml(self):
        buffer = BytesIO()
        with ZipFile(buffer, 'w') as archive:
            archive.writestr('[Content_Types].xml', '<broken')
            archive.writestr('xl/workbook.xml', '<broken')
        with self.assertRaises(WorkbookError):
            compile_workbook(buffer.getvalue())

    def test_expanded_size_limit(self):
        buffer = BytesIO()
        with ZipFile(buffer, 'w', compression=ZIP_DEFLATED) as archive:
            archive.writestr('oversized.txt', b'0' * (20 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(WorkbookError, 'when expanded'):
            compile_workbook(buffer.getvalue())

    def test_output_validation_gates_download(self):
        with patch('src.app_service.validate_config', return_value=['$.factors: rejected']):
            with self.assertRaisesRegex(WorkbookError, 'rejected'):
                compile_workbook(TEMPLATE)


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=10).run()

    def upload(self, name='sample.xlsx', content=TEMPLATE):
        self.app.file_uploader(key='workbook_upload').set_value((name, content, MIME)).run()

    def assert_clean(self):
        self.assertFalse(self.app.exception, [e.message for e in self.app.exception])

    def test_initial_state(self):
        self.assert_clean()
        self.assertTrue(self.app.button(key='generate').disabled)
        self.assertEqual([b.label for b in self.app.download_button], ['Download Excel template'])

    def test_example_flow(self):
        self.app.button(key='example').click().run()
        self.assert_clean()
        self.assertEqual(len(self.app.success), 1)
        self.assertEqual([m.value for m in self.app.metric], ['4', '12', '100%'])
        self.assertEqual([t.label for t in self.app.tabs], ['Overview', 'Rules', 'JSON preview'])
        self.assertEqual(validate_config(json.loads(self.app.code[0].value)), [])
        self.assertIn('json_download', [b.key for b in self.app.download_button])

    def test_upload_flow(self):
        self.upload()
        self.assertFalse(self.app.button(key='generate').disabled)
        self.app.button(key='generate').click().run()
        self.assert_clean()
        self.assertEqual(len(self.app.success), 1)
        self.assertTrue(any('sample.xlsx' in c.value for c in self.app.caption))

    def test_upload_change_clears_previous_output(self):
        self.app.button(key='example').click().run()
        self.upload('bad.xlsx', b'broken workbook')
        self.assertEqual(len(self.app.success), 0)
        self.assertNotIn('json_download', [b.key for b in self.app.download_button])
        self.app.button(key='generate').click().run()
        self.assert_clean()
        self.assertEqual(len(self.app.error), 1)
        self.assertNotIn('json_download', [b.key for b in self.app.download_button])

    def test_clearing_upload_clears_result(self):
        self.upload()
        self.app.button(key='generate').click().run()
        self.app.file_uploader(key='workbook_upload').clear().run()
        self.assert_clean()
        self.assertTrue(self.app.button(key='generate').disabled)
        self.assertEqual(len(self.app.success), 0)
        self.assertNotIn('json_download', [b.key for b in self.app.download_button])

    def test_recover_after_bad_upload(self):
        self.upload('bad.xlsx', b'not a workbook')
        self.app.button(key='generate').click().run()
        self.assertEqual(len(self.app.error), 1)
        self.upload('corrected.xlsx')
        self.app.button(key='generate').click().run()
        self.assert_clean()
        self.assertEqual(len(self.app.error), 0)
        self.assertEqual(len(self.app.success), 1)

    def test_business_error_visible_and_download_blocked(self):
        self.upload()
        with patch('src.app_service.generate', side_effect=ValueError('weight_percent must total 100; got 95')):
            self.app.button(key='generate').click().run()
        self.assert_clean()
        self.assertTrue(any('must total 100' in t.value for t in self.app.text))
        self.assertNotIn('json_download', [b.key for b in self.app.download_button])


if __name__ == '__main__':
    unittest.main()
