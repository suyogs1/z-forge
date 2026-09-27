"""HLASM (High Level Assembler) source parser.

Handles .asm / .hlasm files. Extracts:
- CSECT / DSECT declarations
- DS (Define Storage) fields with labels and computed byte sizes
- DC (Define Constant) fields with labels and byte sizes
- EQU symbols and their values
- COPY references

Not a complete HLASM parser — targets the synthetic-banking CUSTDSCT.ASM patterns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# DS/DC operand size calculation
# ---------------------------------------------------------------------------

# DS/DC type letters → bytes per unit
_TYPE_SIZES: dict[str, int] = {
    "C": 1,  # Character
    "X": 1,  # Hexadecimal
    "B": 1,  # Binary
    "H": 2,  # Halfword
    "F": 4,  # Fullword
    "D": 8,  # Doubleword
    "E": 4,  # Short floating point
    "L": 16,  # Long floating point
    "A": 4,  # Address constant
    "V": 4,  # External address
    "Y": 2,  # Address halfword
    "S": 2,  # Storage operand
    "Q": 4,  # DXD offset
    "P": 1,  # Packed decimal (base — needs digit count)
    "Z": 1,  # Zoned decimal (base)
}

_RE_DS_OPERAND = re.compile(
    r"^(\d*)"  # optional duplication factor
    r"([CXBHFDELASYQPZ])"  # type letter
    r"L?(\d+)?"  # optional length modifier
    r"(?:\(([^)]+)\))?",  # optional operand value in parens
    re.IGNORECASE,
)


def _ds_byte_size(operand: str) -> int:
    """Calculate byte size of a DS/DC operand string like CL8, F, 2H, etc."""
    operand = operand.strip().upper()
    m = _RE_DS_OPERAND.match(operand)
    if not m:
        return 0
    dup = int(m.group(1)) if m.group(1) else 1
    type_ch = m.group(2).upper()
    length_mod = int(m.group(3)) if m.group(3) else None

    base_size = _TYPE_SIZES.get(type_ch, 1)
    if length_mod is not None:
        unit_size = length_mod
    else:
        unit_size = base_size

    return dup * unit_size


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class HlasmField:
    label: str
    opcode: str  # DS, DC, EQU
    operand: str
    byte_size: int = 0
    offset: int = -1  # computed offset within DSECT (or -1 if unknown)
    equ_value: Optional[int] = None  # for EQU symbols
    line: int = 0
    section: str = ""  # owning CSECT/DSECT name


@dataclass
class HlasmSection:
    name: str
    kind: str  # "CSECT" or "DSECT"
    fields: list[HlasmField] = field(default_factory=list)
    line: int = 0


@dataclass
class HlasmParseResult:
    sections: list[HlasmSection] = field(default_factory=list)
    copy_references: list[tuple[str, int]] = field(default_factory=list)
    equ_symbols: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def all_fields(self) -> list[HlasmField]:
        return [f for s in self.sections for f in s.fields]


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_RE_COMMENT = re.compile(r"^\*")  # col 1 asterisk = comment in HLASM
_RE_SECT = re.compile(r"^(\w+)\s+(CSECT|DSECT)\b", re.IGNORECASE)
_RE_DS_DC = re.compile(r"^(\w+)?\s+(D[SC])\s+(.+?)(?:\s+\*.*)?$", re.IGNORECASE)
_RE_EQU = re.compile(r"^(\w+)\s+EQU\s+(.+?)(?:\s+\*.*)?$", re.IGNORECASE)
_RE_COPY_HLASM = re.compile(r"^\s+COPY\s+(\w+)", re.IGNORECASE)
_RE_END = re.compile(r"^\s+END\b", re.IGNORECASE)


def _eval_equ(value_str: str, symbols: dict[str, int]) -> Optional[int]:
    """Try to evaluate a simple EQU expression."""
    v = value_str.strip()
    # *-SYMBOL form (current location minus symbol) — we return None
    if "*" in v and "-" in v:
        return None
    # Pure integer
    if re.match(r"^\d+$", v):
        return int(v)
    # Known symbol
    if v.upper() in symbols:
        return symbols[v.upper()]
    return None


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_hlasm(source: str) -> HlasmParseResult:
    """Parse HLASM source text."""
    result = HlasmParseResult()
    current_section: Optional[HlasmSection] = None
    current_offset = 0

    for lineno, raw in enumerate(source.splitlines(), 1):
        # HLASM comment: * in column 1
        if _RE_COMMENT.match(raw):
            continue
        # Blank lines
        stripped = raw.strip()
        if not stripped:
            continue
        # END statement
        if _RE_END.match(raw):
            break

        # COPY references
        copy_m = _RE_COPY_HLASM.match(raw)
        if copy_m:
            result.copy_references.append((copy_m.group(1).upper(), lineno))
            continue

        # CSECT / DSECT
        sect_m = _RE_SECT.match(raw)
        if sect_m:
            current_section = HlasmSection(
                name=sect_m.group(1).upper(),
                kind=sect_m.group(2).upper(),
                line=lineno,
            )
            result.sections.append(current_section)
            current_offset = 0
            continue

        # EQU
        equ_m = _RE_EQU.match(raw)
        if equ_m:
            label = equ_m.group(1).upper()
            val = _eval_equ(equ_m.group(2), result.equ_symbols)
            if val is not None:
                result.equ_symbols[label] = val
            f = HlasmField(
                label=label,
                opcode="EQU",
                operand=equ_m.group(2).strip(),
                byte_size=0,
                offset=-1,
                equ_value=val,
                line=lineno,
                section=current_section.name if current_section else "",
            )
            if current_section is not None:
                current_section.fields.append(f)
            continue

        # DS / DC
        dsdc_m = _RE_DS_DC.match(raw)
        if dsdc_m:
            label = (dsdc_m.group(1) or "").upper()
            opcode = dsdc_m.group(2).upper()
            operand = dsdc_m.group(3).strip()
            size = _ds_byte_size(operand)
            f = HlasmField(
                label=label,
                opcode=opcode,
                operand=operand,
                byte_size=size,
                offset=(
                    current_offset if current_section and current_section.kind == "DSECT" else -1
                ),
                line=lineno,
                section=current_section.name if current_section else "",
            )
            if current_section is not None:
                current_section.fields.append(f)
            current_offset += size
            continue

    return result


def parse_hlasm_file(path: str | Path) -> HlasmParseResult:
    """Read and parse a HLASM source file."""
    p = Path(path)
    source = p.read_text(encoding="utf-8", errors="replace")
    return parse_hlasm(source)
