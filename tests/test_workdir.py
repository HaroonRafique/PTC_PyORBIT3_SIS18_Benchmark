from pathlib import Path

from common.sis18_lattice import in_workdir


def test_in_workdir_restores_caller_directory(tmp_path: Path):
    original = Path.cwd()
    target = tmp_path / "target"
    target.mkdir()

    with in_workdir(target):
        assert Path.cwd() == target

    assert Path.cwd() == original
