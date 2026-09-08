from pathlib import Path

import pytest

from common.legacy_references import legacy_root, stage_legacy_files


def test_legacy_root_rejects_missing_override(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="SIS18_LEGACY_ROOT"):
        legacy_root({"SIS18_LEGACY_ROOT": str(tmp_path / "absent")})


def test_stage_legacy_files_copies_required_inputs_and_preserves_source(tmp_path: Path):
    source = tmp_path / "legacy"
    input_dir = source / "Step2" / "Input"
    input_dir.mkdir(parents=True)
    for name in ("SIS18.madx", "time.ptc", "chrom.ptc"):
        (input_dir / name).write_text(name, encoding="utf-8")

    staged = stage_legacy_files(step=2, destination=tmp_path / "staged", root=source)

    assert {path.name for path in staged} == {"SIS18.madx", "time.ptc", "chrom.ptc"}
    assert (source / "Step2" / "Input" / "SIS18.madx").read_text(encoding="utf-8") == "SIS18.madx"
    assert (tmp_path / "staged" / "chrom.ptc").read_text(encoding="utf-8") == "chrom.ptc"
