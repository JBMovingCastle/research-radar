from __future__ import annotations

import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock
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

    def test_feishu_markdown_starting_with_front_matter_is_one_argument(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = initialize(Path(temp), preset="blank")
            run_daily(config, date="2026-07-21", adapters=(OneAdapter,))
            completed = SimpleNamespace(returncode=0, stdout="sent", stderr="")
            with (
                mock.patch.dict("os.environ", {"FEISHU_USER_ID": "ou_test"}, clear=False),
                mock.patch("research_radar.delivery.shutil.which", return_value="lark-cli"),
                mock.patch("research_radar.delivery.subprocess.run", return_value=completed) as run,
            ):
                result = deliver(config, "2026-07-21", "feishu")
            self.assertTrue(result["delivery_sent"])
            command = run.call_args.args[0]
            markdown_argument = next(value for value in command if value.startswith("--markdown="))
            self.assertTrue(markdown_argument.startswith("--markdown=---"))


if __name__ == "__main__":
    unittest.main()
