"""COBOL source parser.

Handles .cbl / .cob / .cobol files. Extracts:
- PROGRAM-ID
- DATA DIVISION fields (PIC clauses, byte sizes, level numbers)
- WORKING-STORAGE and LINKAGE data definitions
- COPY statements
- CALL statements
- FILE SELECT/ASSIGN information
- local field declarations (for planted-failure detection)

Not a full COBOL parser — targets the synthetic-banking workspace patterns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# PIC size calculation
# ---------------------------------------------------------------------------

_PIC_REPEATER = re.compile(r"(\w)\((\d+)\)")


def _expand_pic(pic_str: str) -> str:
    """Expand repeater notation: X(8) → XXXXXXXX."""
    return _PIC_REPEATER.sub(lambda m: m.group(1) * int(m.group(2)), pic_str)


def pic_byte_size(pic_str: str) -> int:
    """Return the storage size in bytes for a PIC clause string.

    Handles: X, A, 9, S9, V, COMP, COMP-3, COMP-4, BINARY.
    """
    raw = pic_str.strip().upper()
    # Remove PIC / PICTURE keyword
    raw = re.sub(r"^(PICTURE|PIC)\s*", "", raw)

    # Detect COMP / COMP-3 / COMP-4 / BINARY suffix
    comp3 = bool(re.search(r"COMP-3|PACKED-DECIMAL", raw))
    comp4 = bool(re.search(r"COMP-4|COMP\b|BINARY", raw) and not comp3)

    # Strip COMP suffixes
    raw = re.sub(r"\s*(COMP-[0-9]|COMP|BINARY|PACKED-DECIMAL).*$", "", raw).strip()

    # Expand repeater notation
    raw = _expand_pic(raw)

    # Remove sign and decimal indicators
    raw = raw.replace("S", "").replace("V", "").replace("+", "").replace("-", "")
    raw = raw.replace("$", "").replace(",", "").replace(".", "").replace("Z", "9")
    raw = raw.replace("*", "9").replace("B", "X").replace("0", "X")

    digits = raw.count("9")
    alphas = raw.count("X") + raw.count("A") + raw.count("N")
    total_chars = digits + alphas

    if comp3:
        # COMP-3: ceil((digits + 1) / 2)
        return max(1, (digits + 1 + 1) // 2)
    if comp4:
        # COMP-4 / BINARY: standard sizes by digit count
        if digits <= 4:
            return 2
        if digits <= 9:
            return 4
        return 8

    return max(1, total_chars)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CobolField:
    level: int
    name: str
    pic: str = ""
    byte_size: int = 0
    line: int = 0
    is_88: bool = False
    parent: Optional[str] = None


@dataclass
class FileSelect:
    logical_name: str  # SELECT name
    assign_to: str  # ASSIGN TO target (maps to DD name or dataset)
    line: int = 0


@dataclass
class CobolParseResult:
    program_id: str = ""
    fields: list[CobolField] = field(default_factory=list)
    copy_statements: list[tuple[str, int]] = field(default_factory=list)  # (copybook, line)
    call_statements: list[tuple[str, int]] = field(default_factory=list)  # (program, line)
    file_selects: list[FileSelect] = field(default_factory=list)
    local_declarations: list[CobolField] = field(default_factory=list)  # WS local (non-copy) fields
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_RE_PROGRAM_ID = re.compile(r"^\s*PROGRAM-ID\s*[\.\s]\s*([A-Z0-9#@$-]+)", re.IGNORECASE)
_RE_FIELD_LINE = re.compile(r"^\s*(\d{1,2})\s+([A-Z0-9#@$-]+)(.*?)$", re.IGNORECASE)
_RE_PIC = re.compile(
    r"(PICTURE|PIC)\s+(IS\s+)?([A-Z0-9()+\-VSX.,$*BZN]+(\s+(COMP(?:-[0-9])?|BINARY|PACKED-DECIMAL))?)",
    re.IGNORECASE,
)
_RE_COPY = re.compile(r"^\s*COPY\s+([A-Z0-9#@$-]+)", re.IGNORECASE)
_RE_CALL = re.compile(r"\bCALL\s+['\"]?([A-Z0-9#@$-]+)['\"]?", re.IGNORECASE)
_RE_SELECT = re.compile(
    r"^\s*SELECT\s+([A-Z0-9#@$-]+)\s+ASSIGN\s+TO\s+([A-Z0-9#@$.:_-]+)",
    re.IGNORECASE,
)
_RE_SECTION = re.compile(
    r"^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE|FILE|WORKING-STORAGE|LINKAGE|INPUT-OUTPUT|CONFIGURATION)\s+(DIVISION|SECTION)\s*\.",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_cobol(source: str, path: str = "") -> CobolParseResult:
    """Parse COBOL source text and return a CobolParseResult."""
    result = CobolParseResult()
    lines = source.splitlines()

    in_data_division = False
    in_ws_section = False
    in_procedure = False
    in_file_control = False

    last_copy_line: int = -1

    level_stack: list[tuple[int, str]] = []  # (level, name)

    for lineno, raw in enumerate(lines, 1):
        # Strip comment indicator (columns 1-6 are sequence/indicator area)
        # COBOL fixed format: col 7 is indicator (*=comment, /=page-eject, D=debug)
        if len(raw) > 6 and raw[6] in ("*", "/"):
            continue
        # Sequence area (cols 1-6) and indicator (col 7) — take content from col 8+
        content = raw[6:].rstrip() if len(raw) > 6 else raw.rstrip()

        # ---- Section / division tracking --------------------------------
        sect_m = _RE_SECTION.match(content)
        if sect_m:
            kw = sect_m.group(1).upper()
            div_or_sec = sect_m.group(2).upper()
            if div_or_sec == "DIVISION":
                in_data_division = kw == "DATA"
                in_procedure = kw == "PROCEDURE"
                in_file_control = False
                if not in_data_division:
                    in_ws_section = False
            else:  # SECTION
                in_ws_section = kw == "WORKING-STORAGE"
                if kw == "INPUT-OUTPUT":
                    in_file_control = True
            continue

        # ---- PROGRAM-ID -------------------------------------------------
        if not result.program_id:
            pm = _RE_PROGRAM_ID.match(content)
            if pm:
                result.program_id = pm.group(1).upper()

        # ---- SELECT / ASSIGN (file control) -----------------------------
        if in_file_control:
            sel_m = _RE_SELECT.match(content)
            if sel_m:
                result.file_selects.append(
                    FileSelect(
                        logical_name=sel_m.group(1).upper(),
                        assign_to=sel_m.group(2).upper(),
                        line=lineno,
                    )
                )

        # ---- COPY statements --------------------------------------------
        copy_m = _RE_COPY.match(content)
        if copy_m:
            copybook = copy_m.group(1).upper()
            result.copy_statements.append((copybook, lineno))
            last_copy_line = lineno
            continue

        # ---- CALL statements (procedure division) -----------------------
        if in_procedure:
            for call_m in _RE_CALL.finditer(content):
                prog = call_m.group(1).upper()
                if prog not in ("USING", "BY", "CONTENT", "REFERENCE"):
                    result.call_statements.append((prog, lineno))

        # ---- Data fields ------------------------------------------------
        if in_data_division and not in_procedure:
            fm = _RE_FIELD_LINE.match(content)
            if fm:
                level = int(fm.group(1))
                name = fm.group(2).upper()
                rest = fm.group(3)

                # Skip FILLER and 66/77/88 levels from the field list
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

                # Determine parent
                while level_stack and level_stack[-1][0] >= level:
                    level_stack.pop()
                parent_name = level_stack[-1][1] if level_stack else None
                if level not in (66, 77, 88):
                    level_stack.append((level, name))

                cf = CobolField(
                    level=level,
                    name=name,
                    pic=pic_str,
                    byte_size=byte_sz,
                    line=lineno,
                    is_88=is_88,
                    parent=parent_name,
                )
                result.fields.append(cf)

                # Classify local declarations in WORKING-STORAGE
                # A field is "local" if it appears in WS and was not preceded
                # immediately by a COPY statement on the same or adjacent line
                if in_ws_section and pic_str and level in (1, 77) and not is_88:
                    # Heuristic: if the last COPY was more than 5 lines ago, it's local
                    if last_copy_line < 0 or (lineno - last_copy_line) > 5:
                        result.local_declarations.append(cf)

    return result


# ---------------------------------------------------------------------------
# File-level entry point
# ---------------------------------------------------------------------------


def parse_cobol_file(path: str | Path) -> CobolParseResult:
    """Read and parse a COBOL source file."""
    p = Path(path)
    source = p.read_text(encoding="utf-8", errors="replace")
    return parse_cobol(source, str(path))
