from pathlib import Path

import pytest

from common.sis18_config import format_resolved_config, load_step_config


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


def test_standalone_step_config_inherits_reference_profile(tmp_path: Path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '''{
  "step": 6,
  "profiles": {
    "reference": {"intensity": 2.95e10, "n_macroparticles": 1, "turns": 15000, "sextupole_enabled": true, "qx": 4.3504, "qy": 3.2, "restoring_force": -1.951e-11, "distribution": "single_particle"},
    "smoke": {"turns": 64}
  }
}''',
        encoding="utf-8",
    )

    smoke = load_step_config(config_path, step=6, profile="smoke")

    assert smoke.turns == 64
    assert smoke.intensity == 2.95e10
    assert (smoke.qx, smoke.qy) == (4.3504, 3.2)


def test_resolved_config_display_includes_merged_profile_and_step_inputs(tmp_path: Path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '''{
  "step": 6,
  "profiles": {
    "reference": {"turns": 15000, "launch": {"x_m": 0.005}},
    "smoke": {"turns": 64}
  },
  "physics": {"space_charge": "analytical_frozen_gaussian"}
}''',
        encoding="utf-8",
    )

    display = format_resolved_config(config_path, step=6, profile="smoke")

    assert '"profile": "smoke"' in display
    assert '"turns": 64' in display
    assert '"x_m": 0.005' in display
    assert '"space_charge": "analytical_frozen_gaussian"' in display


def test_step_2_uses_public_bare_tunes():
    reference = load_step_config(ROOT / "step_02_tunes_no_sextupole" / "config.json", step=2, profile="reference")

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


def test_step_7_uses_the_fast_scattering_bare_tunes():
    reference = load_step_config(ROOT / "shared_inputs" / "benchmark_profiles.json", step=7, profile="reference")

    assert (reference.qx, reference.qy) == (4.3504, 3.2)
    assert reference.turns == 2000


def test_step_8_reference_profile_uses_the_published_one_hundred_thousand_turn_case():
    reference = load_step_config(ROOT / "step_08_long_term_trapping" / "config.json", step=8, profile="reference")
    artifact = load_step_config(ROOT / "step_08_long_term_trapping" / "config.json", step=8, profile="legacy_artifact")

    assert (reference.qx, reference.qy) == (4.3504, 3.2)
    assert reference.turns == 100_000
    assert artifact.turns == 200_000
