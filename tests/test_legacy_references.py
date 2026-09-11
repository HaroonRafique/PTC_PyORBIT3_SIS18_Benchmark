from pathlib import Path

import pytest

from common.reference_artifacts import maybe_reference_root, reference_root, stage_packaged_inputs


def test_reference_root_rejects_missing_override(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="SIS18_REFERENCE_ROOT"):
        reference_root({"SIS18_REFERENCE_ROOT": str(tmp_path / "absent")})


def test_reference_root_is_not_needed_when_comparison_is_disabled():
    assert maybe_reference_root(None, comparison_enabled=False) is None


def test_stage_packaged_inputs_copies_local_inputs(tmp_path: Path):
    input_dir = tmp_path / "step" / "legacy_input"
    input_dir.mkdir(parents=True)
    for name in ("SIS18.madx", "time.ptc", "chrom.ptc"):
        (input_dir / name).write_text(name, encoding="utf-8")

    staged = stage_packaged_inputs(source=input_dir, destination=tmp_path / "staged")

    assert {path.name for path in staged} == {"SIS18.madx", "time.ptc", "chrom.ptc"}
    assert (input_dir / "SIS18.madx").read_text(encoding="utf-8") == "SIS18.madx"
    assert (tmp_path / "staged" / "chrom.ptc").read_text(encoding="utf-8") == "chrom.ptc"
