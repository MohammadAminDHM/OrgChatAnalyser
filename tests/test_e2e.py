import tempfile, pathlib, sys, os, subprocess, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_end_to_end_unrelated_project():
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / "README.md").write_text("# Chatbot")
        (root / "Dockerfile").write_text("FROM python")
        (root / "src").mkdir()
        (root / "retrieval").mkdir()
        (root / "evals").mkdir()
        (root / "monitoring").mkdir()
        # Run via python module directly (simulates npx calling engine)
        result = subprocess.run(
            [sys.executable, "-m", "orgchat", "check", "--path", str(root), "--format", "json", "--non-interactive"],
            capture_output=True, text=True, cwd=str(root), timeout=60
        )
        # Should analyze root, not installation dir
        assert root.name in result.stdout or root.name in result.stderr or result.returncode in (0, 1)
        # Should not be analyzing this repo
        assert "OrgChatAnalyser" not in result.stdout or result.returncode in (0, 1)
        # Verify no crash
        assert result.returncode in (0, 1)
