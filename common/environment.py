"""Runtime resolution and PTC-PyORBIT3 import staging."""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import os
from pathlib import Path
import shutil
import sys


DEFAULT_PYORBIT3_ROOT = Path("/home/hr/Codes/PTC_PyORBIT3_Codex_Merge_Jul26/PyORBIT3")
DEFAULT_MADX = Path("/home/hr/Codes/PTC_PyORBIT3_Codex_Merge_Jul26/ptc_pyorbit3_examples/tools/madx/madx-linux64_v5_02_00")


@dataclass(frozen=True)
class RuntimePaths:
    pyorbit3_root: Path
    madx: Path


def resolve_runtime_paths(
    *, pyorbit3_root: Path = DEFAULT_PYORBIT3_ROOT, madx: Path = DEFAULT_MADX
) -> RuntimePaths:
    """Validate and resolve the PyORBIT3 and MAD-X runtime paths."""

    pyorbit3_root = pyorbit3_root.resolve()
    madx = madx.resolve()
    if not pyorbit3_root.is_dir():
        raise FileNotFoundError(f"PyORBIT3 root does not exist: {pyorbit3_root}")
    if not madx.is_file() or not os.access(madx, os.X_OK):
        raise FileNotFoundError(f"MAD-X executable is unavailable or not executable: {madx}")
    return RuntimePaths(pyorbit3_root=pyorbit3_root, madx=madx)


def prepare_pyorbit3_runtime(paths: RuntimePaths, runtime_dir: Path) -> Path:
    """Stage a PTC-enabled Meson build into a self-contained import layout."""

    build_dir = paths.pyorbit3_root / "build" / "ptc-enabled-config"
    source_py = paths.pyorbit3_root / "py"
    source_extensions = build_dir / "src"
    libptc = build_dir / "subprojects" / "libptc_orbit" / "libptc_orbit.so"
    libcore = source_extensions / "libcore.so"
    required = (source_py, source_extensions, libptc, libcore)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing PTC-PyORBIT3 runtime inputs: " + ", ".join(missing))

    runtime_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_py, runtime_dir, dirs_exist_ok=True)
    core_dir = runtime_dir / "orbit" / "core"
    core_dir.mkdir(parents=True, exist_ok=True)
    for extension in source_extensions.glob("*.so"):
        target = runtime_dir / extension.name if extension.name.startswith("pylibptc_orbit") else core_dir / extension.name
        target.unlink(missing_ok=True)
        target.symlink_to(extension)
    for library in (libptc, libcore):
        ctypes.CDLL(str(library), mode=ctypes.RTLD_GLOBAL)
    if str(runtime_dir) not in sys.path:
        sys.path.insert(0, str(runtime_dir))
    return runtime_dir


def verify_ptc_runtime(paths: RuntimePaths, runtime_dir: Path) -> dict[str, str]:
    """Import the PTC-enabled API and return a concise runtime identity."""

    prepare_pyorbit3_runtime(paths, runtime_dir)
    import orbit  # noqa: F401
    import pylibptc_orbit  # noqa: F401
    from orbit.core.bunch import Bunch
    from ext.ptc_orbit import PTC_Lattice

    Bunch()
    PTC_Lattice("sis18_runtime_smoke")
    return {"pyorbit3_root": str(paths.pyorbit3_root), "runtime_dir": str(runtime_dir)}
