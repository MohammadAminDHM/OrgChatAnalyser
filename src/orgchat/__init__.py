"""OrgChat project readiness checker."""
try:
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("orgchat")
except PackageNotFoundError:
    __version__ = "0.1.4"
