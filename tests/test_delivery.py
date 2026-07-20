from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_radar.config import initialize
from research_radar.delivery import deliver
from research_radar.models import PaperCandidate, SourceResult
from research_radar.pipeline import run_daily


class OneAdapter:
    id = "one"

    def collect(self, context):
        return SourceResult(
            self.id,
            "success",
            [PaperCandidate(source="crossref", title="Artificial intelligence research", abstract="Artificial intelligence research", published_date=context.today.isoformat())],
        )


class DeliveryTests(unittest.TestCase):
    def test_local_delivery_records_one_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = initialize(Path(temp), preset="blank")
            run_daily(config, date="2026-07-21", adapters=(OneAdapter,))
            first = deliver(config, "2026-07-21", "local")
            self.assertTrue(first["delivery_sent"])
            second = deliver(config, "2026-07-21", "local")
            self.assertTrue(second["idempotent_skip"])


if __name__ == "__main__":
    unittest.main()
