from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile
import unittest

from orgchat.checker import build_report
from orgchat.report import render_json, render_markdown


HEALTHY_CONFIG = f'''[project]
name = "Test Chatbot"

[data_sources]
sources = ["minio://docs"]
freshness_slo_minutes = 1440
sync_monitoring = true
owner = "Data team"
refresh_test = true

[access_control]
auth = "OIDC"
rbac = true
document_level_filters = true
audit_log = true
secret_scan = true

[quality]
eval_dataset = "evals/golden.jsonl"
automated_eval = true
regression_gate = true
min_score = 0.8
last_evaluation = "{date.today().isoformat()}"

[grounding]
citations = true
abstention = true
fallback = true
prompt_injection_defense = true
retrieval_logging = true

[observability]
tracing = true
token_cost_tracking = true
request_metrics = true
latency_slo_ms = 2000
dashboard = "ops/dashboard.json"

[monitoring]
healthcheck = "/health"
error_logging = true
alerts = true
backup_restore_test = true
incident_runbook = "docs/incident-runbook.md"

[ownership]
service_owner = "AI Platform"
technical_owner = "Tech lead"
oncall = "on-call"
runbook = "docs/runbook.md"
review_cadence = "monthly"
'''


class CheckerTests(unittest.TestCase):
    def test_healthy_project_scores_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evals").mkdir()
            (root / "ops").mkdir()
            (root / "docs").mkdir()
            (root / "evals/golden.jsonl").write_text("{}\n", encoding="utf-8")
            (root / "ops/dashboard.json").write_text("{}", encoding="utf-8")
            (root / "docs/incident-runbook.md").write_text("# incidents", encoding="utf-8")
            (root / "docs/runbook.md").write_text("# runbook", encoding="utf-8")
            (root / "orgchat.toml").write_text(HEALTHY_CONFIG, encoding="utf-8")

            report = build_report(root)

            self.assertEqual(report.overall_status, "PASS")
            self.assertEqual(report.score, 100.0)
            self.assertIn("هر هفت محور", report.analysis)
            self.assertTrue(all(check.status == "PASS" for check in report.checks))

    def test_missing_configuration_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = build_report(directory)

            self.assertEqual(report.overall_status, "WARN")
            self.assertEqual(report.score, 0.0)
            self.assertIn("orgchat.toml", report.analysis)
            self.assertGreater(len(report.next_actions), 0)

    def test_renderers_return_expected_formats(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = build_report(directory)
            self.assertIn('"overall_status": "WARN"', render_json(report))
            self.assertIn("# OrgChat Check", render_markdown(report))


if __name__ == "__main__":
    unittest.main()
