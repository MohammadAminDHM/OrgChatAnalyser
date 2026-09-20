import json, pathlib, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_version_sync():
    import orgchat
    import importlib.metadata
    npm = json.load(open('npm-wrapper/package.json'))
    py_ver = importlib.metadata.version('orgchat')
    init_ver = orgchat.__version__
    # All must exist and match expected 0.1.2 for this release
    assert npm['version'] == py_ver == init_ver, f"Version drift: npm={npm['version']} py={py_ver} init={init_ver}"
