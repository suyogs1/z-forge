"""Z-FORGE snapshot management and deterministic hashing.

Rules:
- Original imported artifacts in workspace are IMMUTABLE.
- All changes go into snapshots/<snapshot-id>/.
- Deterministic SHA-256 hashes are used for tamper-evident tracking.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from zforge.models import Artifact, ArtifactType, Snapshot

_EXCLUDED_SNAPSHOT_DIRS = {
    "snapshots",
    "reports",
    "graph",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
_EXCLUDED_SNAPSHOT_FILES = {"zforge.pack.json"}


def hash_bytes(data: bytes) -> str:
    """Return 16-character hex digest of data."""
    return hashlib.sha256(data).hexdigest()[:16]


def hash_file(file_path: Path) -> str:
    """Compute deterministic SHA-256 hash of a file."""
    if not file_path.exists():
        return ""
    data = file_path.read_bytes()
    return hash_bytes(data)


def hash_directory(dir_path: Path) -> str:
    """Compute deterministic SHA-256 hash across all files in dir_path."""
    if not dir_path.exists():
        return ""
    all_files: list[Path] = [
        p for p in dir_path.rglob("*") if p.is_file() and not p.name.endswith(".json")
    ]
    all_files.sort(key=lambda p: p.relative_to(dir_path).as_posix())

    hasher = hashlib.sha256()
    for f in all_files:
        rel = f.relative_to(dir_path).as_posix()
        file_hash = hash_file(f)
        hasher.update(f"{rel}:{file_hash}".encode())
    return hasher.hexdigest()[:16]


def create_snapshot(
    workspace_root: Path | str,
    label: str,
    snapshot_id: str,
    base_snapshot_id: str | None = None,
    proposals_applied: list[str] | None = None,
    timestamp: str | None = None,
) -> Snapshot:
    """Create a new snapshot directory and manifest.

    If base_snapshot_id is provided, copies from that snapshot's directory.
    Otherwise copies original artifacts from workspace_root.
    Original files are NEVER mutated.
    """
    ws_root = Path(workspace_root).resolve()
    snapshots_dir = ws_root / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    target_dir = snapshots_dir / snapshot_id
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if base_snapshot_id:
        src_dir = snapshots_dir / base_snapshot_id
        if not src_dir.exists():
            raise FileNotFoundError(f"Base snapshot does not exist: {src_dir}")
        for item in src_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, target_dir / item.name)
            elif item.is_file() and not item.name.endswith(".json"):
                shutil.copy2(item, target_dir / item.name)
    else:
        for item in ws_root.iterdir():
            if item.name in _EXCLUDED_SNAPSHOT_DIRS or item.name in _EXCLUDED_SNAPSHOT_FILES:
                continue
            if item.is_dir():
                shutil.copytree(item, target_dir / item.name)
            elif item.is_file():
                shutil.copy2(item, target_dir / item.name)

    # Compute artifact hashes
    artifacts_map: dict[str, str] = {}
    for f in sorted(target_dir.rglob("*")):
        if f.is_file() and not f.name.endswith(".json"):
            rel = f.relative_to(target_dir).as_posix()
            # Determine artifact type
            ext = f.suffix.lower()
            art_type = ArtifactType.UNKNOWN
            if ext in (".cbl", ".cob"):
                art_type = ArtifactType.COBOL
            elif ext in (".cpy", ".copy"):
                art_type = ArtifactType.COPYBOOK
            elif ext in (".asm", ".hlasm"):
                art_type = ArtifactType.HLASM
            elif ext == ".jcl":
                art_type = ArtifactType.JCL
            elif ext in (".dsd", ".dat"):
                art_type = ArtifactType.DATASET
            elif ext == ".afp":
                art_type = ArtifactType.AFP

            art_id = Artifact.make_id(rel, art_type)
            artifacts_map[art_id] = hash_file(f)

    ws_hash = hash_directory(target_dir)
    snap_time = timestamp if timestamp is not None else "2024-01-15T00:00:00Z"

    snapshot = Snapshot(
        id=snapshot_id,
        label=label,
        timestamp=snap_time,
        workspace_hash=ws_hash,
        proposals_applied=proposals_applied or [],
        artifacts=artifacts_map,
    )

    # Save snapshot metadata JSON
    meta_path = snapshots_dir / f"{snapshot_id}.json"
    meta_path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")

    return snapshot


def _safe_unlink(path: Path, max_retries: int = 5) -> None:
    import time

    for attempt in range(max_retries):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            if attempt == max_retries - 1:
                raise
            time.sleep(0.05)


def _safe_rmtree(path: Path, max_retries: int = 5) -> None:
    import time

    for attempt in range(max_retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if attempt == max_retries - 1:
                raise
            time.sleep(0.05)


def reset_workspace(workspace_root: Path | str) -> list[str]:
    """Safely remove generated snapshots and reports.

    NEVER touches original imported artifacts (cobol, copybooks, etc.).
    Returns list of removed paths.
    """
    ws_root = Path(workspace_root).resolve()
    removed: list[str] = []

    for dir_name in ("snapshots", "reports"):
        target = ws_root / dir_name
        if target.exists():
            for item in target.iterdir():
                if item.is_dir():
                    _safe_rmtree(item)
                    removed.append(f"{dir_name}/{item.name}/")
                elif item.is_file():
                    _safe_unlink(item)
                    removed.append(f"{dir_name}/{item.name}")
        else:
            target.mkdir(parents=True, exist_ok=True)

    return removed


