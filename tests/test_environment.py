from pathlib import Path

import pytest

from common.environment import resolve_runtime_paths


def test_runtime_paths_use_explicit_overrides(tmp_path: Path):
    pyorbit3 = tmp_path / "PyORBIT3"
    madx = tmp_path / "madx"
    legacy = tmp_path / "legacy"
    pyorbit3.mkdir()
    legacy.mkdir()
    madx.write_text("", encoding="utf-8")
    madx.chmod(0o755)

    paths = resolve_runtime_paths(pyorbit3_root=pyorbit3, madx=madx, legacy=legacy)

    assert paths.pyorbit3_root == pyorbit3.resolve()
    assert paths.madx == madx.resolve()
    assert paths.legacy_root == legacy.resolve()


def test_runtime_paths_reject_non_executable_madx(tmp_path: Path):
    pyorbit3 = tmp_path / "PyORBIT3"
    legacy = tmp_path / "legacy"
    madx = tmp_path / "madx"
    pyorbit3.mkdir()
    legacy.mkdir()
    madx.write_text("", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="MAD-X"):
        resolve_runtime_paths(pyorbit3_root=pyorbit3, madx=madx, legacy=legacy)
