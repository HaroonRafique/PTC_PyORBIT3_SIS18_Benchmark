from pathlib import Path

import pytest

from common.sis18_lattice import required_flat_file


def test_required_flat_file_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="PTC flat file"):
        required_flat_file(tmp_path / "missing.flt")
