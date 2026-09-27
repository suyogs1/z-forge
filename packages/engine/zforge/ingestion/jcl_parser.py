"""JCL (Job Control Language) parser.

Handles .jcl files. Extracts:
- JOB card metadata
- EXEC statements (PGM and PROC)
- DD statements (DDNAME, DSN, DISP, LRECL, BLKSIZE, RECFM)
- Dataset producers and consumers (inferred from DISP)

Not a complete JCL parser — targets the synthetic-banking workspace patterns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class JclDD:
    ddname: str
    dsn: str = ""
    disp: str = ""
    lrecl: int = 0
    blksize: int = 0
    recfm: str = ""
    step_name: str = ""
    line: int = 0

    @property
    def is_output(self) -> bool:
        """True when the DISP indicates the dataset is being written."""
        d = self.disp.upper()
        return "NEW" in d or "MOD" in d

    @property
    def is_input(self) -> bool:
        """True when the DISP indicates the dataset is being read."""
        d = self.disp.upper()
        return "SHR" in d or "OLD" in d or (not self.is_output and bool(d))


@dataclass
class JclStep:
    name: str
    pgm: str = ""
    proc: str = ""
    line: int = 0
    dds: list[JclDD] = field(default_factory=list)


@dataclass
class JclParseResult:
    job_name: str = ""
    steps: list[JclStep] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def all_dds(self) -> list[JclDD]:
        return [dd for step in self.steps for dd in step.dds]

    def dataset_producers(self) -> list[tuple[str, str]]:
        """Return list of (program_name, dataset_name) for output datasets."""
        result = []
        for step in self.steps:
            if step.pgm:
                for dd in step.dds:
                    if dd.dsn and dd.is_output:
                        result.append((step.pgm, dd.dsn))
        return result

    def dataset_consumers(self) -> list[tuple[str, str]]:
        """Return list of (program_name, dataset_name) for input datasets."""
        result = []
        for step in self.steps:
            if step.pgm:
                for dd in step.dds:
                    if dd.dsn and dd.is_input:
                        result.append((step.pgm, dd.dsn))
        return result


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_RE_COMMENT = re.compile(r"^//\*")
_RE_JOB = re.compile(r"^//(\w+)\s+JOB\b", re.IGNORECASE)
_RE_EXEC = re.compile(r"^//(\w+)\s+EXEC\s+(.+?)(?:\s*,.*)?$", re.IGNORECASE)
_RE_DD = re.compile(r"^//(\w+)\s+DD\s+(.*?)$", re.IGNORECASE)
_RE_CONTINUATION = re.compile(r"^//\s{12,}(.+)$")  # // + 12+ spaces = col 16+ (JCL continuation)

# Parameter extraction
_RE_PGM = re.compile(r"\bPGM=(\w+)", re.IGNORECASE)
_RE_PROC = re.compile(r"^//\w+\s+EXEC\s+(\w+)(?!\s*=)", re.IGNORECASE)
_RE_DSN = re.compile(r"\bDSN=([^,\s)]+)", re.IGNORECASE)
_RE_DISP = re.compile(r"\bDISP=(\(([^)]+)\)|(\w+))", re.IGNORECASE)
_RE_LRECL = re.compile(r"\bLRECL=(\d+)", re.IGNORECASE)
_RE_BLKSIZE = re.compile(r"\bBLKSIZE=(\d+)", re.IGNORECASE)
_RE_RECFM = re.compile(r"\bRECFM=(\w+)", re.IGNORECASE)


def _extract_disp(text: str) -> str:
    """Extract DISP value from a JCL parameter string."""
    m = _RE_DISP.search(text)
    if not m:
        return ""
    # Prefer group 2 (paren form) else group 3 (bare word)
    return (m.group(2) or m.group(3) or "").strip()


def _extract_dsn(text: str) -> str:
    m = _RE_DSN.search(text)
    return m.group(1).strip() if m else ""


def _parse_dcb_and_inline(text: str) -> tuple[str, int, int]:
    """Return (recfm, lrecl, blksize) from inline or DCB= params."""
    recfm_m = _RE_RECFM.search(text)
    lrecl_m = _RE_LRECL.search(text)
    blksize_m = _RE_BLKSIZE.search(text)
    recfm = recfm_m.group(1) if recfm_m else ""
    lrecl = int(lrecl_m.group(1)) if lrecl_m else 0
    blksize = int(blksize_m.group(1)) if blksize_m else 0
    return recfm, lrecl, blksize


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_jcl(source: str) -> JclParseResult:
    """Parse JCL source text."""
    result = JclParseResult()
    current_step: Optional[JclStep] = None
    current_dd: Optional[JclDD] = None

    def flush_statement(stmt: str, lineno: int) -> None:
        nonlocal current_step, current_dd

        if _RE_COMMENT.match(stmt):
            return

        job_m = _RE_JOB.match(stmt)
        if job_m:
            result.job_name = job_m.group(1).upper()
            return

        exec_m = _RE_EXEC.match(stmt)
        if exec_m:
            step_name = exec_m.group(1).upper()
            exec_params = exec_m.group(2).strip()
            pgm = ""
            proc = ""
            pgm_m = _RE_PGM.search(exec_params)
            if pgm_m:
                pgm = pgm_m.group(1).upper()
            else:
                proc_m = _RE_PROC.match(stmt)
                if proc_m:
                    proc = proc_m.group(1).upper()
            current_step = JclStep(name=step_name, pgm=pgm, proc=proc, line=lineno)
            result.steps.append(current_step)
            current_dd = None
            return

        dd_m = _RE_DD.match(stmt)
        if dd_m:
            ddname = dd_m.group(1).upper()
            dd_params = dd_m.group(2)
            dsn = _extract_dsn(dd_params)
            disp = _extract_disp(dd_params)
            recfm, lrecl, blksize = _parse_dcb_and_inline(dd_params)
            step_name = current_step.name if current_step else ""
            current_dd = JclDD(
                ddname=ddname,
                dsn=dsn,
                disp=disp,
                lrecl=lrecl,
                blksize=blksize,
                recfm=recfm,
                step_name=step_name,
                line=lineno,
            )
            if current_step is not None:
                current_step.dds.append(current_dd)
            return

        # SYSIN inline data between /* */ — skip
        # Continuation lines are handled by accumulation above

    lines = source.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        lineno = i + 1

        # Inline data (not a JCL statement)
        if not raw.startswith("//"):
            i += 1
            continue

        # Accumulate continuation lines
        accumulated = raw
        while (
            i + 1 < len(lines)
            and lines[i + 1].startswith("//")
            and _RE_CONTINUATION.match(lines[i + 1])
        ):
            i += 1
            accumulated = accumulated.rstrip() + " " + lines[i].strip()

        flush_statement(accumulated, lineno)
        i += 1

    return result


def parse_jcl_file(path: str | Path) -> JclParseResult:
    """Read and parse a JCL file."""
    p = Path(path)
    source = p.read_text(encoding="utf-8", errors="replace")
    return parse_jcl(source)
