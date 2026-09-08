"""PTC flat-file validation and SIS18 lattice loading helpers."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
from typing import Any


@contextmanager
def in_workdir(path: Path):
    """Run a PTC operation in its step-local artifact directory."""

    original = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original)


def required_flat_file(path: Path) -> Path:
    """Resolve a required PTC flat file or fail with an actionable message."""

    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"PTC flat file is missing: {path}")
    return path


def load_sis18_lattice(flat_file: Path) -> tuple[Any, Any]:
    """Load a PTC lattice and synchronize a fresh PyORBIT3 bunch with PTC."""

    from orbit.core.bunch import Bunch
    from ext.ptc_orbit import PTC_Lattice
    from ext.ptc_orbit.ptc_orbit import setBunchParamsPTC

    flat_file = required_flat_file(flat_file)
    lattice = PTC_Lattice("SIS18")
    with in_workdir(flat_file.parent):
        lattice.readPTC(str(flat_file))
    bunch = Bunch()
    setBunchParamsPTC(bunch)
    if lattice.getLength() <= 0.0 or lattice.nNodes <= 0:
        raise RuntimeError("PTC loaded an invalid SIS18 lattice with no length or nodes")
    return lattice, bunch
