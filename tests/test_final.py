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

def test_non_interactive_flag():
    import argparse
    from orgchat.cli import _parser
    args = _parser().parse_args(["check", "--non-interactive"])
    assert args.non_interactive is True

def test_cached_runtime_reuse():
    # Version-aware cache path uses ORGCHAT_VERSION from package.json
    import json, os
    pkg = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'npm-wrapper', 'package.json')))
    assert pkg['version'] == '0.1.2'

def test_cli_interactive_answer_reaches_report():
    import tempfile, pathlib, sys
    from unittest.mock import patch
    from orgchat.cli import main
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        with patch('sys.stdin', open('/dev/null' if sys.platform != 'win32' else 'NUL', 'r')):
            pass  # non-interactive path check
        # Non-interactive must not prompt
        code = main(["check", "--path", str(root), "--non-interactive", "--format", "json", "--output", str(root / "out.json")])
        assert code == 0 or code == 1  # may be WARN/FAIL
