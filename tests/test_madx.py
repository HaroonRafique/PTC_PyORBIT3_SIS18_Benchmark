from pathlib import Path

from common.madx import generate_flat_file


def test_generate_flat_file_runs_madx_in_step_local_workdir(tmp_path: Path):
    executable = tmp_path / "madx"
    executable.write_text("#!/bin/sh\ntouch SIS_18_BENCHMARK.flt\n", encoding="utf-8")
    executable.chmod(0o755)
    workdir = tmp_path / "step_input"
    workdir.mkdir()
    source = workdir / "SIS18.madx"
    source.write_text("title;\n", encoding="utf-8")

    flat_file = generate_flat_file(madx=executable, workdir=workdir, madx_input=source)

    assert flat_file == workdir / "SIS_18_BENCHMARK.flt"
    assert flat_file.is_file()
    assert (workdir / "madx.log").is_file()


def test_generate_flat_file_accepts_legacy_input_subdirectory(tmp_path: Path):
    executable = tmp_path / "madx"
    executable.write_text("#!/bin/sh\ntouch SIS_18_BENCHMARK.flt\n", encoding="utf-8")
    executable.chmod(0o755)
    workdir = tmp_path / "step_input"
    source = workdir / "Input" / "SIS18.madx"
    source.parent.mkdir(parents=True)
    source.write_text("title;\n", encoding="utf-8")

    assert generate_flat_file(madx=executable, workdir=workdir, madx_input=source).is_file()
