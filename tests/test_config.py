from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research_radar.config import ConfigError, doctor, initialize, load_config


class ConfigTests(unittest.TestCase):
    def test_init_and_doctor_work_without_api_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = initialize(root, preset="ci3")
            config, resolved = load_config(path)
            self.assertEqual(resolved, path)
            self.assertFalse(config["sources"]["openalex"]["enabled"])
            ok, checks = doctor(path)
            self.assertTrue(ok, checks)
            self.assertTrue((root / config["paths"]["briefs_dir"]).is_dir())

    def test_rejects_unsafe_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = initialize(root, preset="blank")
            data = json.loads(path.read_text(encoding="utf-8"))
            data["paths"]["briefs_dir"] = "../outside"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "Unsafe repository path"):
                load_config(path)

    def test_rejects_invalid_issn_and_empty_queries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = initialize(root, preset="blank")
            data = json.loads(path.read_text(encoding="utf-8"))
            data["target_sources"] = [{"name": "Bad", "issn": "123"}]
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "Invalid ISSN"):
                load_config(path)
            data["target_sources"] = []
            data["tracks"][0]["queries"] = []
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "at least one query"):
                load_config(path)

    def test_accepts_custom_daily_limit_and_rejects_invalid_report_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = initialize(Path(temp), preset="blank")
            data = json.loads(path.read_text(encoding="utf-8"))
            data["selection"]["daily_limit"] = 8
            path.write_text(json.dumps(data), encoding="utf-8")
            load_config(path)
            data["selection"]["daily_limit"] = 21
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "1 to 20"):
                load_config(path)
            data["selection"]["daily_limit"] = 5
            data["report"]["item_fields"] = ["not-a-field"]
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "report.item_fields"):
                load_config(path)

    def test_rejects_invalid_timezone(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = initialize(Path(temp), preset="blank")
            data = json.loads(path.read_text(encoding="utf-8"))
            data["project"]["timezone"] = "Not/A-Timezone"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "Invalid project.timezone"):
                load_config(path)

    def test_rejects_non_object_source_without_crashing_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = initialize(Path(temp), preset="blank")
            data = json.loads(path.read_text(encoding="utf-8"))
            data["sources"]["crossref"] = True
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "sources.crossref must be an object"):
                load_config(path)
            ok, checks = doctor(path)
            self.assertFalse(ok)
            self.assertIn("sources.crossref must be an object", checks[-1]["detail"])

    def test_invalid_json_reports_location(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "line 1"):
                load_config(path)

    def test_requires_at_least_one_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = initialize(Path(temp), preset="blank")
            data = json.loads(path.read_text(encoding="utf-8"))
            for name in ("crossref", "arxiv", "semantic_scholar", "openalex"):
                data["sources"][name]["enabled"] = False
            data["sources"]["feeds"] = []
            data["sources"]["web_pages"] = []
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "At least one"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
