"""Dataset schema parser.

Handles:
- .dsd  — JSON dataset schema descriptors
- .dat  — fixed-width sample data files

Preserves field names, offsets, lengths, and type information.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DatasetField:
    name: str
    field_type: str = "X"  # COBOL type shorthand: X, 9, S9, etc.
    length: int = 0
    offset: int = 0
    pic: str = ""
    description: str = ""
    source_field: Optional[str] = None  # cross-reference to source field


@dataclass
class DcbInfo:
    recfm: str = ""
    lrecl: int = 0
    blksize: int = 0


@dataclass
class DatasetParseResult:
    dataset_name: str = ""
    record_name: str = ""
    copybook: str = ""  # copybook reference if documented
    program: str = ""  # producing program if documented
    dcb: DcbInfo = field(default_factory=DcbInfo)
    fields: list[DatasetField] = field(default_factory=list)
    sample_records: list[bytes] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# .dsd (JSON) parser
# ---------------------------------------------------------------------------


def parse_dsd(source: str, path: str = "") -> DatasetParseResult:
    """Parse a JSON dataset schema descriptor (.dsd)."""
    result = DatasetParseResult()
    try:
        doc: dict[str, Any] = json.loads(source)
    except json.JSONDecodeError as exc:
        result.warnings.append(f"JSON parse error in {path}: {exc}")
        return result

    result.dataset_name = doc.get("dataset_name", "")
    result.record_name = doc.get("record_name", "")
    result.copybook = doc.get("copybook", "")
    result.program = doc.get("program", "")

    dcb_raw = doc.get("dcb", {})
    result.dcb = DcbInfo(
        recfm=dcb_raw.get("recfm", ""),
        lrecl=dcb_raw.get("lrecl", 0),
        blksize=dcb_raw.get("blksize", 0),
    )

    for f in doc.get("fields", []):
        result.fields.append(
            DatasetField(
                name=f.get("name", ""),
                field_type=f.get("type", "X"),
                length=f.get("length", 0),
                offset=f.get("offset", 0),
                pic=f.get("pic", ""),
                description=f.get("description", ""),
                source_field=f.get("source_field"),
            )
        )

    return result


def parse_dsd_file(path: str | Path) -> DatasetParseResult:
    """Read and parse a .dsd JSON schema file."""
    p = Path(path)
    source = p.read_text(encoding="utf-8", errors="replace")
    return parse_dsd(source, str(p))


# ---------------------------------------------------------------------------
# .dat (fixed-width) sample parser
# ---------------------------------------------------------------------------


def parse_dat_file(path: str | Path, lrecl: int = 0) -> DatasetParseResult:
    """Read a fixed-width .dat sample data file.

    If *lrecl* is 0 the record length is inferred from the first line.
    Sample data is stored as raw bytes for downstream analysis.
    """
    p = Path(path)
    result = DatasetParseResult(dataset_name=p.stem)

    try:
        raw = p.read_bytes()
    except OSError as exc:
        result.warnings.append(f"Cannot read {path}: {exc}")
        return result

    # Split on newlines; each non-empty line is one record
    for line in raw.splitlines():
        if line:
            result.sample_records.append(line)

    if result.sample_records and lrecl == 0:
        lrecl = len(result.sample_records[0])
    result.dcb.lrecl = lrecl

    return result


# ---------------------------------------------------------------------------
# Combined loader (tries .dsd first, .dat as supplement)
# ---------------------------------------------------------------------------


def load_dataset(
    dsd_path: str | Path | None = None,
    dat_path: str | Path | None = None,
) -> DatasetParseResult:
    """Load dataset schema from .dsd and optionally supplement with .dat sample."""
    result: Optional[DatasetParseResult] = None

    if dsd_path is not None and Path(dsd_path).exists():
        result = parse_dsd_file(dsd_path)

    if dat_path is not None and Path(dat_path).exists():
        dat_result = parse_dat_file(dat_path, lrecl=result.dcb.lrecl if result else 0)
        if result is None:
            result = dat_result
        else:
            result.sample_records = dat_result.sample_records

    if result is None:
        result = DatasetParseResult()

    return result
