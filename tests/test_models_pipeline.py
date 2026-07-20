from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research_radar.config import initialize
from research_radar.models import PaperCandidate, SourceResult
from research_radar.pipeline import annotate_and_filter, merge_duplicates, run_daily


class GoodAdapter:
    id = "fixture-good"

    def collect(self, context):
        return SourceResult(
            self.id,
            "success",
            [
                PaperCandidate(
                    source="crossref",
                    title="Human-robot collaboration for modular construction",
                    authors=["Ada Example"],
                    abstract="Collaborative robot assembly in prefabricated construction and smart construction.",
                    published_date=context.today.isoformat(),
                    year=context.today.year,
                    doi="https://doi.org/10.1000/example",
                    venue="Automation in Construction",
                    issn=["0926-5805"],
                    url="https://doi.org/10.1000/example",
                    citation_count=2,
                    evidence_level="abstract",
                )
            ],
        )


class DuplicateAdapter:
    id = "fixture-duplicate"

    def collect(self, context):
        return SourceResult(
            self.id,
            "success",
            [
                PaperCandidate(
                    source="semantic_scholar",
                    title="Human-robot collaboration for modular construction",
                    abstract="A longer abstract about human robot collaboration in modular construction and robotic assembly.",
                    published_date=context.today.isoformat(),
                    doi="10.1000/example",
                    url="https://example.org/paper",
                )
            ],
        )


class BrokenAdapter:
    id = "fixture-broken"

    def collect(self, context):
        raise RuntimeError("fixture provider outage")


class ModelPipelineTests(unittest.TestCase):
    def test_canonical_doi_and_merge(self) -> None:
        first = PaperCandidate(source="a", title="Same", doi="https://doi.org/10.1/ABC", abstract="short")
        second = PaperCandidate(source="b", title="Same", doi="10.1/abc", abstract="a much longer abstract")
        merged = merge_duplicates([first, second])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].canonical_id, "doi:10.1/abc")
        self.assertEqual(merged[0].sources, ["a", "b"])
        self.assertEqual(merged[0].abstract, "a much longer abstract")

    def test_venue_only_filters_non_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config_path = initialize(Path(temp), preset="ci3")
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["selection"]["venue_mode"] = "only"
            off_target = PaperCandidate(source="crossref", title="Modular construction robot", abstract="human robot collaboration", venue="Other Journal")
            target = PaperCandidate(source="crossref", title="Modular construction robot", abstract="human robot collaboration", venue="Automation in Construction")
            self.assertFalse(annotate_and_filter(off_target, config))
            self.assertTrue(annotate_and_filter(target, config))

    def test_run_is_idempotent_and_provider_failure_is_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = initialize(root, preset="ci3")
            first = run_daily(config_path, date="2026-07-21", adapters=(GoodAdapter, DuplicateAdapter, BrokenAdapter))
            self.assertTrue(first["brief_written"])
            self.assertEqual(first["selected_count"], 1)
            self.assertEqual(first["coverage"], "partial")
            self.assertFalse(Path(first["brief_path"]).is_absolute())
            brief = root / first["brief_path"]
            self.assertIn("source_status: \"partial\"", brief.read_text(encoding="utf-8"))
            second = run_daily(config_path, date="2026-07-21", adapters=(GoodAdapter,))
            self.assertTrue(second["idempotent_skip"])
            ledger = root / "90-system/index/recommendation-ledger.jsonl"
            self.assertEqual(len(ledger.read_text(encoding="utf-8").splitlines()), 1)

    def test_run_force_rebuilds_same_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = initialize(root, preset="ci3")
            run_daily(config_path, date="2026-07-21", adapters=(GoodAdapter,))
            rebuilt = run_daily(config_path, date="2026-07-21", adapters=(GoodAdapter,), force=True)
            self.assertEqual(rebuilt["selected_count"], 1)
            ledger = root / "90-system/index/recommendation-ledger.jsonl"
            self.assertEqual(len(ledger.read_text(encoding="utf-8").splitlines()), 1)

    def test_report_template_fields_and_requirements_are_configurable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = initialize(root, preset="blank")
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["context_keywords"] = ["construction"]
            config["tracks"][0]["keywords"] = ["robot"]
            config["report"] = {
                "writing_requirements": ["保留论文链接。"],
                "item_fields": ["authors", "doi", "abstract"],
                "abstract_limit": 20,
                "style": {
                    "intro": "面向例会的简短速览。",
                    "requirements_heading": "编辑规则",
                    "selection_heading": "本期重点",
                    "analysis_heading": "证据边界",
                },
            }
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = run_daily(config_path, date="2026-07-21", adapters=(GoodAdapter,))
            brief = (root / result["brief_path"]).read_text(encoding="utf-8")
            self.assertIn("面向例会的简短速览。", brief)
            self.assertIn("## 编辑规则", brief)
            self.assertIn("保留论文链接。", brief)
            self.assertIn("## 本期重点", brief)
            self.assertIn("## 证据边界", brief)
            self.assertNotIn("- **评分：**", brief)


if __name__ == "__main__":
    unittest.main()
