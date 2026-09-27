"""Copybook parser.

Reuses the COBOL data-definition parser to extract fields and byte sizes
from .cpy / .copy copybook files.  A copybook is essentially a partial
COBOL DATA DIVISION fragment (no PROGRAM-ID, no PROCEDURE DIVISION).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from zforge.ingestion.cobol_parser import (
    _RE_COPY,
    _RE_FIELD_LINE,
    _RE_PIC,
    CobolField,
    CobolParseResult,
    pic_byte_size,
)


@dataclass
class CopybookParseResult:
    name: str = ""  # Copybook name derived from filename
    fields: list[CobolField] = field(default_factory=list)
    copy_statements: list[tuple[str, int]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_copybook(source: str, name: str = "") -> CopybookParseResult:
    """Parse a COBOL copybook fragment."""
    result = CopybookParseResult(name=name)
    lines = source.splitlines()

    level_stack: list[tuple[int, str]] = []

    for lineno, raw in enumerate(lines, 1):
        # Skip comment lines (fixed-format col 7 == '*' or '/')
        if len(raw) > 6 and raw[6] in ("*", "/"):
            continue
        content = raw[6:].rstrip() if len(raw) > 6 else raw.rstrip()

        # COPY statements within copybooks (e.g. ACCTMAST COPY CUSTMAST)
        copy_m = _RE_COPY.match(content)
        if copy_m:
            result.copy_statements.append((copy_m.group(1).upper(), lineno))
            continue

        fm = _RE_FIELD_LINE.match(content)
        if not fm:
            continue

        level = int(fm.group(1))
        name_f = fm.group(2).upper()
        rest = fm.group(3)

        is_88 = level == 88

        pic_m = _RE_PIC.search(rest)
        pic_str = ""
        byte_sz = 0
        if pic_m:
            pic_str = pic_m.group(0)
            try:
                byte_sz = pic_byte_size(pic_str)
            except Exception:
                byte_sz = 0

        while level_stack and level_stack[-1][0] >= level:
            level_stack.pop()
        parent_name = level_stack[-1][1] if level_stack else None
        if level not in (66, 77, 88):
            level_stack.append((level, name_f))

        result.fields.append(
            CobolField(
                level=level,
                name=name_f,
                pic=pic_str,
                byte_size=byte_sz,
                line=lineno,
                is_88=is_88,
                parent=parent_name,
            )
        )

    return result


def parse_copybook_file(path: str | Path) -> CopybookParseResult:
    """Read and parse a COBOL copybook file."""
    p = Path(path)
    source = p.read_text(encoding="utf-8", errors="replace")
    cpy_name = p.stem.upper()
    return parse_copybook(source, name=cpy_name)


def resolve_copybook_fields(
    cobol_result: CobolParseResult,
    copybooks: dict[str, CopybookParseResult],
) -> list[CobolField]:
    """Return all fields from a COBOL program with copybook fields inlined.

    For each COPY statement in the COBOL source, if the named copybook is
    present in *copybooks*, its fields are appended.  The original program
    fields (non-copy) are included as-is.
    """
    resolved: list[CobolField] = list(cobol_result.fields)
    for copybook_name, _lineno in cobol_result.copy_statements:
        key = copybook_name.upper().removesuffix(".CPY")
        if key in copybooks:
            resolved.extend(copybooks[key].fields)
    return resolved
