import json
from pathlib import Path

from common.reference_artifacts import sha256_file


ROOT = Path(__file__).resolve().parents[1]


def test_step_1_website_reference_manifest_hashes_downloaded_images():
    directory = ROOT / "shared_inputs" / "reference_plots" / "step_01"
    manifest = json.loads((directory / "reference_manifest.json").read_text(encoding="utf-8"))

    assert manifest["source_page"].endswith("1-benchmarking-phase-space.html")
    assert [entry["label"] for entry in manifest["plots"]] == [
        "MICROMAP & SIMPSONS",
        "ORBIT",
        "MADX+ORBITPTC",
    ]
    for entry in manifest["plots"]:
        assert entry["url"].startswith("http://www-linux.gsi.de/~giuliano/")
        assert sha256_file(directory / entry["file"]) == entry["sha256"]


def test_step_2_website_reference_manifest_hashes_downloaded_images():
    directory = ROOT / "shared_inputs" / "reference_plots" / "step_02"
    manifest = json.loads((directory / "reference_manifest.json").read_text(encoding="utf-8"))

    assert manifest["source_page"].endswith("2-benchmarking-tunes_vs_xy.html")
    assert [entry["label"] for entry in manifest["plots"]] == ["Horizontal tune vs x", "Vertical tune vs y"]
    for entry in manifest["plots"]:
        assert entry["url"].startswith("http://www-linux.gsi.de/~giuliano/")
        assert sha256_file(directory / entry["file"]) == entry["sha256"]


def test_step_3_website_reference_manifest_hashes_downloaded_images():
    directory = ROOT / "shared_inputs" / "reference_plots" / "step_03"
    manifest = json.loads((directory / "reference_manifest.json").read_text(encoding="utf-8"))

    assert manifest["source_page"].endswith("3-benchmarking-tunes_vs_x_sex-on-qx4338.html")
    assert [entry["label"] for entry in manifest["plots"]] == ["Horizontal tune vs x", "Vertical tune vs y"]
    for entry in manifest["plots"]:
        assert entry["url"].startswith("http://www-linux.gsi.de/~giuliano/")
        assert sha256_file(directory / entry["file"]) == entry["sha256"]


def test_step_4_website_reference_manifest_hashes_downloaded_images():
    directory = ROOT / "shared_inputs" / "reference_plots" / "step_04"
    manifest = json.loads((directory / "reference_manifest.json").read_text(encoding="utf-8"))

    assert manifest["source_page"].endswith("4-benchmarking-tunes_vs_x_sex-on.html")
    assert [entry["label"] for entry in manifest["plots"]] == ["Horizontal tune vs x", "Vertical tune vs y"]
    for entry in manifest["plots"]:
        assert entry["url"].startswith("http://www-linux.gsi.de/~giuliano/")
        assert sha256_file(directory / entry["file"]) == entry["sha256"]


def test_step_5_website_reference_manifest_hashes_downloaded_images():
    directory = ROOT / "shared_inputs" / "reference_plots" / "step_05"
    manifest = json.loads((directory / "reference_manifest.json").read_text(encoding="utf-8"))

    assert manifest["source_page"].endswith("5-ps-sc-sex-on.html")
    assert [entry["label"] for entry in manifest["plots"]] == ["MICROMAP", "SIMPSONS", "Synergia"]
    for entry in manifest["plots"]:
        assert entry["url"].startswith("http://www-linux.gsi.de/~giuliano/")
        assert sha256_file(directory / entry["file"]) == entry["sha256"]
