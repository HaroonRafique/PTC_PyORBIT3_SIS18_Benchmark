"""Read-only staging utilities for historical SIS18 benchmark artifacts."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
from typing import Mapping


DEFAULT_LEGACY_ROOT = Path("/home/hr/Repositories/PTC_PyORBIT_SIS18_Benchmark")


def legacy_root(environ: Mapping[str, str] | None = None) -> Path:
    """Return the configured read-only legacy benchmark root."""

    environment = os.environ if environ is None else environ
    root = Path(environment.get("SIS18_LEGACY_ROOT", str(DEFAULT_LEGACY_ROOT))).expanduser()
    if not root.is_dir():
        raise FileNotFoundError(f"SIS18_LEGACY_ROOT does not exist or is not a directory: {root}")
    return root.resolve()


def sha256_file(path: Path) -> str:
    """Return a stable SHA-256 digest without loading the whole file in memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage_legacy_files(*, step: int, destination: Path, root: Path) -> list[Path]:
    """Copy the PTC/MAD-X files needed by a step into its local staging area.

    Missing optional files are ignored so focused tests and reduced historical
    checkouts remain usable. Source files are always copied, never moved.
    """

    source = root / f"Step{step}" / "Input"
    if not source.is_dir():
        raise FileNotFoundError(f"Legacy input directory is missing: {source}")
    names = ["SIS18.madx", "SIS18.seq", "time.ptc", "resplit.ptc", "print_flat_file.ptc"]
    if step == 2:
        names.append("chrom.ptc")
    destination.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    for name in names:
        candidate = source / name
        if candidate.is_file():
            target = destination / name
            shutil.copy2(candidate, target)
            staged.append(target)
    if not staged:
        raise FileNotFoundError(f"No known SIS18 input files were found in {source}")
    return staged
