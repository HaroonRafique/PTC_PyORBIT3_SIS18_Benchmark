"""Portable PyORBIT MPI helpers mirroring the examples repository API."""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MPIContext:
    """Small wrapper around PyORBIT MPI with a serial fallback."""

    comm: Any
    rank: int
    size: int
    enabled: bool

    @property
    def is_master(self) -> bool:
        """Whether this is rank zero."""

        return self.rank == 0


def environment_rank() -> int:
    """Return rank from standard MPI launcher environment variables."""

    for key in ("OMPI_COMM_WORLD_RANK", "PMI_RANK", "PMIX_RANK", "MV2_COMM_WORLD_RANK"):
        value = os.environ.get(key)
        if value is not None:
            try:
                return int(value)
            except ValueError:
                pass
    return 0


def environment_size() -> int:
    """Return size from standard MPI launcher environment variables."""

    for key in ("OMPI_COMM_WORLD_SIZE", "PMI_SIZE", "PMIX_SIZE", "MV2_COMM_WORLD_SIZE"):
        value = os.environ.get(key)
        if value is not None:
            try:
                return max(1, int(value))
            except ValueError:
                pass
    return 1


def orbit_mpi_module() -> Any:
    """Import PyORBIT MPI from either supported runtime layout."""

    errors: list[str] = []
    for module_name in ("orbit_mpi", "orbit.core.orbit_mpi"):
        try:
            return importlib.import_module(module_name)
        except Exception as error:
            errors.append(f"{module_name}: {error}")
    raise ImportError("Could not import PyORBIT MPI (" + "; ".join(errors) + ")")


def get_mpi_context(enabled: bool = True, comm: Any | None = None) -> MPIContext:
    """Return active PyORBIT MPI context, with a serial fallback."""

    if not enabled:
        return MPIContext(comm=None, rank=0, size=1, enabled=False)
    env_rank, env_size = environment_rank(), environment_size()
    try:
        orbit_mpi = orbit_mpi_module()
        active_comm = comm if comm is not None else orbit_mpi.mpi_comm.MPI_COMM_WORLD
        context = MPIContext(
            comm=active_comm,
            rank=int(orbit_mpi.MPI_Comm_rank(active_comm)),
            size=int(orbit_mpi.MPI_Comm_size(active_comm)),
            enabled=True,
        )
    except Exception as error:
        if env_size > 1:
            raise RuntimeError("MPI launcher is active but PyORBIT MPI is unavailable") from error
        return MPIContext(comm=None, rank=env_rank, size=env_size, enabled=False)
    if env_size > 1 and context.size != env_size:
        raise RuntimeError(f"MPI launcher reports {env_size} ranks, but PyORBIT reports {context.size}")
    return context


def barrier(context: MPIContext) -> None:
    """Synchronize active MPI ranks."""

    if context.enabled and context.size > 1:
        orbit_mpi_module().MPI_Barrier(context.comm)


def master_print(message: str, context: MPIContext, *, flush: bool = True) -> None:
    """Print exactly once from rank zero."""

    if context.is_master:
        print(message, flush=flush)


def local_count_for_rank(global_count: int, context: MPIContext) -> int:
    """Return this rank's balanced share of a configured global count."""

    if global_count < 0:
        raise ValueError("global_count must be non-negative")
    base, remainder = divmod(int(global_count), max(1, int(context.size)))
    return base + (1 if context.rank < remainder else 0)


def local_counts_for_size(*, global_count: int, size: int) -> list[int]:
    """Return every rank's balanced share of a global count."""

    if global_count < 0 or size < 1:
        raise ValueError("global_count must be non-negative and size must be positive")
    base, remainder = divmod(int(global_count), int(size))
    return [base + (1 if rank < remainder else 0) for rank in range(size)]


def rank_log_path(log_dir: Path, context: MPIContext, stem: str = "run_example") -> Path:
    """Return the examples-style rank-specific log path."""

    return Path(log_dir) / f"{stem}.rank{context.rank:04d}.log"
