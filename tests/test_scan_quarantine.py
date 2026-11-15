import gzip
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from scan_quarantine import unpack_checked
class ScanBoundaryTests(unittest.TestCase):
    def test_hash_mismatch_refused(self):
        with self.assertRaises(ValueError): unpack_checked(gzip.compress(b'changed'),'0'*64)
    def test_expansion_limit_refused(self):
        with self.assertRaises(ValueError): unpack_checked(gzip.compress(b'A'*100),hashlib.sha256(b'A'*100).hexdigest(),10)
    def test_exact_verified_bytes_returned(self):
        body=b'%PDF-1.7\n%%EOF'
        self.assertEqual(unpack_checked(gzip.compress(body),hashlib.sha256(body).hexdigest()),body)
