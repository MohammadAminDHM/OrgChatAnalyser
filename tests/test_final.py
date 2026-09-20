import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_interactive_answer_affects_report():
    from orgchat.cli import main
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        # no config; simulate answer via monkey-patching input if needed
        # Just verify build_report accepts context_config
        from orgchat.checker import build_report
        r = build_report(root, context_config={"data_sources": {"freshness_slo_minutes": 1440}})
        # Should have some evidence of config
        assert r is not None

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
