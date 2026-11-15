import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_data", ROOT / "scripts" / "build_data.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TestDataValidation(unittest.TestCase):
    def test_data_exports(self):
        exported = MODULE.validate_and_export()
        self.assertGreaterEqual(len(exported["sources"]), 5)
        self.assertGreaterEqual(len(exported["observations"]), 4)
        self.assertTrue(all(obs["source_ids"] for obs in exported["observations"]))

    def test_export_is_current(self):
        data = MODULE.validate_and_export()
        expected = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        self.assertEqual((ROOT / "public" / "data" / "dashboard.json").read_text(encoding="utf-8"), expected)

    def test_source_links_https(self):
        sources = MODULE.read_json("source_registry.json")
        self.assertTrue(all(x["url"].startswith("https://") for x in sources))


if __name__ == "__main__":
    unittest.main()
