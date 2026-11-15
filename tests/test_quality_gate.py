"""Regression tests for the dependency-free repository hygiene gate."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("quality_gate", ROOT / "scripts" / "quality_gate.py")
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class QualityGateTests(unittest.TestCase):
    def test_generated_artifacts_and_credentials_are_forbidden(self):
        for filename in ("dist/index.html", "release/app.exe", ".collection/a.gz", ".env",
                         ".env.production", "secrets/cert.pem", "a/.private.key"):
            with self.subTest(filename=filename):
                self.assertIsNotNone(gate.disallowed_path(Path(filename)))

    def test_safe_example_and_normal_code_are_allowed(self):
        for filename in (".env.example", "src/main.tsx", "data/knowledge_graph.json"):
            with self.subTest(filename=filename):
                self.assertIsNone(gate.disallowed_path(Path(filename)))

    def test_detects_real_private_key_markers_and_conflicts(self):
        self.assertIn("private key material", gate.scan_text("-----BEGIN " + "PRIVATE KEY-----\nAAAA"))
        self.assertIn("unresolved merge conflict", gate.scan_text("<<<<<<< HEAD\nchange\n=======\nother\n>>>>>>> main"))

    def test_ordinary_public_document_and_placeholders_pass(self):
        self.assertEqual([], gate.scan_text("See https://example.org and set R2_SECRET_ACCESS_KEY in GitHub Secrets"))

    def test_token_pattern(self):
        token = "ghp_" + "A" * 36
        self.assertIn("GitHub credential token", gate.scan_text("const secret = " + token))


if __name__ == "__main__":
    unittest.main()
