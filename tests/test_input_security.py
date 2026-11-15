import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from input_security import validate_upload, source_url, clean_text, MAX_UPLOAD
from upload_requests import requests_for
from intake_upload import intake
from collect import LocalStore


class IntakeSecurity(unittest.TestCase):
    def test_only_allowlisted_content_types(self):
        for name, body in [('report.pdf', b'<script>alert(1)</script>'), ('run.exe', b'MZ'), ('archive.zip', b'PK')]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_upload(name, body)

    def test_paths_and_windows_streams_rejected(self):
        for name in ('../a.csv', 'a\\b.csv', 'a.csv:stream'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_upload(name, b'a,b\n1,2')

    def test_pdf_active_content_rejected(self):
        with self.assertRaises(ValueError):
            validate_upload('x.pdf', b'%PDF-1.7\n/JavaScript (evil)\n%%EOF')

    def test_csv_formula_and_binary_rejected(self):
        for body in (b'name,value\na,=1+1', b'name,value\na,\x00', b'a,b\n1'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                validate_upload('x.csv', body)

    def test_size_and_controls_rejected(self):
        with self.assertRaises(ValueError):
            validate_upload('x.csv', b'x' * (MAX_UPLOAD + 1))
        with self.assertRaises(ValueError):
            clean_text('filename\x00')

    def test_links_do_not_allow_scripts_or_credentials(self):
        for url in ('javascript:alert(1)', 'data:text/html,a', 'https://user:password@example.org'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                source_url(url)

    def test_valid_file_remains_quarantined_and_unscanned(self):
        self.assertEqual(validate_upload('table.csv', b'a,b\n1,2')['review_state'], 'quarantined')
        self.assertEqual(validate_upload('table.csv', b'a,b\n1,2')['scan_state'], 'not_scanned')

    def test_intake_rejects_unknown_request_before_storage(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'Unknown upload request'):
                intake('nonexistent', 'invented', 'https://example.org', '2026-01-01T00:00:00Z', LocalStore(temp), [])

    def test_only_missing_essential_requirements_request_upload(self):
        cases = [{'case_id': 'case', 'requirements': [{'id': 'a', 'label': 'Original report', 'capability': 'report_body', 'routes': [{'source_id': 'source'}]}]}]
        gates = {'case': {'requirements': [{'id': 'a', 'met': False, 'essential': True}]}}
        self.assertEqual(requests_for(cases, gates)[0]['document'], 'Original report')
        gates['case']['requirements'][0]['met'] = True
        self.assertEqual(requests_for(cases, gates), [])
