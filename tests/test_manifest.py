import json
from pathlib import Path

from common.manifest import write_run_manifest


def test_write_run_manifest_is_sorted_and_creates_parent(tmp_path: Path):
    path = write_run_manifest(tmp_path / "nested" / "manifest.json", {"z": 1, "a": {"step": 2}})

    assert path == tmp_path / "nested" / "manifest.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": {"step": 2}, "z": 1}
    assert path.read_text(encoding="utf-8").splitlines()[1].startswith('  "a"')
