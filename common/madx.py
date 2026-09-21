"""Small MAD-X execution helper with step-local output discipline."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess


def generate_flat_file(*, madx: Path, workdir: Path, madx_input: Path) -> Path:
    """Run MAD-X in ``workdir`` and return the historical PTC flat file."""

    workdir = workdir.resolve()
    madx_input = madx_input.resolve()
    try:
        madx_input.relative_to(workdir)
    except ValueError as exc:
        raise ValueError("MAD-X input must be staged beneath its step-local workdir") from exc
    log_path = workdir / "madx.log"
    with madx_input.open("rb") as stream, log_path.open("wb") as log:
        subprocess.run([str(madx)], cwd=workdir, stdin=stream, stdout=log, stderr=subprocess.STDOUT, check=True)
    flat_file = workdir / "SIS_18_BENCHMARK.flt"
    if not flat_file.is_file():
        raise RuntimeError(f"MAD-X completed without producing expected PTC flat file; see {log_path}")
    return flat_file


def set_madx_bare_tunes(path: Path, *, qx: float, qy: float) -> Path:
    """Set staged PTC-match fractional tunes from explicit full bare tunes."""

    text = path.read_text(encoding="utf-8")
    replacements = {"Q1": qx % 1.0, "Q2": qy % 1.0}
    for plane, fractional_tune in replacements.items():
        pattern = rf"(table\(ptc_twiss_summary,{plane}\)=\s*)[-+0-9.eE]+(;)"
        text, count = re.subn(pattern, rf"\g<1>{fractional_tune:.10g}\g<2>", text, count=1)
        if count != 1:
            raise ValueError(f"staged MAD-X input has no unique {plane} tune constraint: {path}")
    path.write_text(text, encoding="utf-8")
    return path
