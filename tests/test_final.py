import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_interactive_answer_affects_report():
    import tempfile, pathlib
    from orgchat.checker import build_report
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        # No config => data_sources fresh is missing -> WARN
        before = build_report(root)
        # After interactive answer: set freshness_slo
        after = build_report(root, context_config={"data_sources": {"freshness_slo_minutes": 1440}})
        # Find the data_sources finding
        before_fresh = None
        after_fresh = None
        for c in before.checks:
            if c.key == "data_sources":
                for f in c.findings:
                    if f.key == "freshness_slo_minutes":
                        before_fresh = f.status
        for c in after.checks:
            if c.key == "data_sources":
                for f in c.findings:
                    if f.key == "freshness_slo_minutes":
                        after_fresh = f.status
        assert before_fresh == "WARN"
        assert after_fresh == "PASS"
        assert after.score > before.score

def test_no_config_discovery():
    from orgchat.config import discover_project
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / "README.md").write_text("x")
        ev = discover_project(root)
        assert "README.md" in ev

def test_non_interactive_never_calls_input():
    import tempfile, pathlib, sys, json
    from unittest.mock import patch
    from orgchat.cli import main
    def fail_input(*a, **k):
        raise AssertionError("input() must not be called in non-interactive mode")
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        out_path = root / "non_interactive.json"
        with patch('builtins.input', fail_input):
            with patch('sys.stdin.isatty', return_value=False):
                code = main(["check", "--path", str(root), "--non-interactive", "--format", "json", "--output", str(out_path)])
        assert out_path.exists()
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert code in (0, 1)

def test_node_launcher_version_sync():
    import json, os
    pkg = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'npm-wrapper', 'package.json')))
    import orgchat
    import importlib.metadata
    assert pkg['version'] == importlib.metadata.version('orgchat') == orgchat.__version__

def test_non_tty_never_calls_input():
    import tempfile, pathlib, sys
    from unittest.mock import patch
    from orgchat.cli import main
    def fail_input(*a, **k):
        raise AssertionError("input() must not be called when stdin is not TTY")
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        with patch('builtins.input', fail_input):
            with patch('sys.stdin.isatty', return_value=False):
                code = main(["check", "--path", str(root), "--format", "json"])
        assert code in (0, 1)

def test_cli_interactive_answer_reaches_report():
    import tempfile, pathlib, sys, json
    from unittest.mock import patch
    from orgchat.cli import main
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        with patch('builtins.input', return_value='y') as mocked_input:
            with patch('sys.stdin.isatty', return_value=True):
                code = main(["check", "--path", str(root), "--format", "json", "--output", str(root / "after.json")])
        mocked_input.assert_called_once()
        assert code in (0, 1)
        report_path = root / "after.json"
        assert report_path.exists()
        data = json.loads(report_path.read_text(encoding="utf-8"))
        for check in data.get("checks", []):
            if check.get("key") == "data_sources":
                for finding in check.get("findings", []):
                    if finding.get("key") == "freshness_slo_minutes":
                        assert finding.get("status") == "PASS", f"Expected PASS, got {finding.get('status')}"
                        break
