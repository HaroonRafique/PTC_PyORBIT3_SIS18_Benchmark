"""Packaged SIS18 input staging and read-only reference artifact access."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
from typing import Mapping


DEFAULT_REFERENCE_ROOT = Path("/home/hr/Repositories/PTC_PyORBIT_SIS18_Benchmark")


def reference_root(environ: Mapping[str, str] | None = None) -> Path:
    """Return the configured read-only historical comparison root."""

    environment = os.environ if environ is None else environ
    root = Path(environment.get("SIS18_REFERENCE_ROOT", str(DEFAULT_REFERENCE_ROOT))).expanduser()
    if not root.is_dir():
        raise FileNotFoundError(f"SIS18_REFERENCE_ROOT does not exist or is not a directory: {root}")
    return root.resolve()


def maybe_reference_root(path: Path | None, *, comparison_enabled: bool) -> Path | None:
    """Resolve a comparison root only when a run requests comparisons."""

    if not comparison_enabled:
        return None
    if path is None:
        return reference_root()
    path = path.expanduser()
    if not path.is_dir():
        raise FileNotFoundError(f"SIS18_REFERENCE_ROOT does not exist or is not a directory: {path}")
    return path.resolve()


def sha256_file(path: Path) -> str:
    """Return a stable SHA-256 digest without loading the whole file in memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage_packaged_inputs(*, source: Path, destination: Path) -> list[Path]:
    """Copy tracked step-local inputs to a MAD-X workspace without external access."""

    if not source.is_dir():
        raise FileNotFoundError(f"Packaged SIS18 input directory is missing: {source}")
    destination.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    for candidate in sorted(source.iterdir()):
        if candidate.is_file():
            target = destination / candidate.name
            shutil.copy2(candidate, target)
            staged.append(target)
    if not staged:
        raise FileNotFoundError(f"No packaged SIS18 input files were found in {source}")
    return staged
