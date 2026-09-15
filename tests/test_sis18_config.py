from pathlib import Path

import pytest

from common.sis18_config import load_step_config


ROOT = Path(__file__).resolve().parents[1]


def test_smoke_profile_preserves_step_physics_and_reduces_cost(tmp_path: Path):
    profiles = tmp_path / "profiles.json"
    profiles.write_text(
        """{
  "steps": {
    "2": {
      "intensity": 2.95e10,
      "n_macroparticles": 100,
      "turns": 1024,
      "sextupole_enabled": false,
      "qx": 3.2,
      "qy": 4.338,
      "profile_overrides": {"smoke": {"n_macroparticles": 8, "turns": 16}}
    }
  }
}""",
        encoding="utf-8",
    )

    reference = load_step_config(profiles, step=2, profile="reference")
    smoke = load_step_config(profiles, step=2, profile="smoke")

    assert smoke.sextupole_enabled is reference.sextupole_enabled is False
    assert smoke.qx == reference.qx == 3.2
    assert smoke.qy == reference.qy == 4.338
    assert smoke.turns < reference.turns
    assert smoke.n_macroparticles < reference.n_macroparticles


def test_unknown_profile_is_rejected(tmp_path: Path):
    profiles = tmp_path / "profiles.json"
    profiles.write_text('{"steps": {"1": {}}}', encoding="utf-8")

    with pytest.raises(ValueError, match="profile"):
        load_step_config(profiles, step=1, profile="fast")


def test_step_2_uses_public_bare_tunes():
    reference = load_step_config(ROOT / "shared_inputs" / "benchmark_profiles.json", step=2, profile="reference")

    assert reference.qx == 4.338
    assert reference.qy == 3.2


def test_step_3_uses_public_bare_tunes():
    reference = load_step_config(ROOT / "shared_inputs" / "benchmark_profiles.json", step=3, profile="reference")

    assert reference.qx == 4.338
    assert reference.qy == 3.2


def test_step_4_uses_the_resonance_crossing_bare_tunes():
    reference = load_step_config(ROOT / "shared_inputs" / "benchmark_profiles.json", step=4, profile="reference")

    assert reference.qx == 4.3504
    assert reference.qy == 3.2


def test_step_5_uses_the_phase_space_island_bare_tunes():
    reference = load_step_config(ROOT / "shared_inputs" / "benchmark_profiles.json", step=5, profile="reference")

    assert reference.qx == 4.3504
    assert reference.qy == 3.2


def test_step_6_published_and_legacy_artifact_profiles_have_distinct_launches():
    profiles = ROOT / "shared_inputs" / "benchmark_profiles.json"

    reference = load_step_config(profiles, step=6, profile="reference")
    artifact = load_step_config(profiles, step=6, profile="legacy_artifact")

    assert (reference.qx, reference.qy) == (4.3504, 3.2)
    assert reference.turns == artifact.turns == 15000
    assert reference.profile == "reference"
    assert artifact.profile == "legacy_artifact"
