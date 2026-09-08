from pathlib import Path


def test_required_benchmark_directories_exist():
    root = Path(__file__).parents[1]
    assert (root / "common").is_dir()
    assert (root / "shared_inputs").is_dir()
    for number in range(1, 10):
        assert list(root.glob(f"step_{number:02d}_*"))
