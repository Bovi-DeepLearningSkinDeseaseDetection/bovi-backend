from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bovi-backend")
except PackageNotFoundError:  # pragma: no cover - only when running without installing
    __version__ = "dev"
