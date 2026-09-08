from pathlib import Path

from common.sis18_diagnostics import TurnRecord, write_diagnostics


def test_write_diagnostics_creates_step_local_csv(tmp_path: Path):
    path = write_diagnostics(tmp_path / "output", [TurnRecord(turn=0, x=1.0, xp=2.0, z=3.0, dE=4.0, action_x=5.0)])

    assert path == tmp_path / "output" / "turn_diagnostics.csv"
    assert "action_x" in path.read_text(encoding="utf-8")
