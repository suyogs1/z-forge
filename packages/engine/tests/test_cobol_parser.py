"""Unit tests for COBOL parser."""

from __future__ import annotations

from zforge.ingestion.cobol_parser import parse_cobol, pic_byte_size

# ---------------------------------------------------------------------------
# PIC size tests
# ---------------------------------------------------------------------------


def test_pic_alpha_x8() -> None:
    assert pic_byte_size("PIC X(8)") == 8


def test_pic_alpha_x30() -> None:
    assert pic_byte_size("PIC X(30)") == 30


def test_pic_9() -> None:
    assert pic_byte_size("PIC 9(6)") == 6


def test_pic_comp_3() -> None:
    # S9(4) COMP-3 → ceil((4+1)/2) = 3
    assert pic_byte_size("PIC S9(4) COMP-3") == 3


def test_pic_comp_4_small() -> None:
    # S9(4) COMP → 2 bytes
    assert pic_byte_size("PIC S9(4) COMP") == 2


def test_pic_comp_4_medium() -> None:
    # S9(9) COMP → 4 bytes
    assert pic_byte_size("PIC S9(9) COMP") == 4


def test_pic_xx() -> None:
    assert pic_byte_size("PIC XX") == 2


def test_pic_s9_13_v99_comp3() -> None:
    # S9(13)V99 → 15 digits, COMP-3: ceil(16/2) = 8
    size = pic_byte_size("PIC S9(13)V99 COMP-3")
    assert size == 8


# ---------------------------------------------------------------------------
# PROGRAM-ID extraction
# ---------------------------------------------------------------------------


ACCTPROG_SNIPPET = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ACCTPROG.
       AUTHOR. ZENITH-BANK-SYNTHETIC.
"""


def test_program_id_extracted() -> None:
    result = parse_cobol(ACCTPROG_SNIPPET)
    assert result.program_id == "ACCTPROG"


# ---------------------------------------------------------------------------
# COPY statement extraction
# ---------------------------------------------------------------------------


COPY_SNIPPET = """\
       DATA DIVISION.
       FILE SECTION.
       FD  ACCOUNT-FILE
           RECORD CONTAINS 80 CHARACTERS.
           COPY ACCTMAST.
       WORKING-STORAGE SECTION.
           COPY ERRCODE.
"""


def test_copy_statements_found() -> None:
    result = parse_cobol(COPY_SNIPPET)
    names = [c for c, _ in result.copy_statements]
    assert "ACCTMAST" in names
    assert "ERRCODE" in names


# ---------------------------------------------------------------------------
# CALL statement extraction
# ---------------------------------------------------------------------------


CALL_SNIPPET = """\
       PROCEDURE DIVISION.
       MAIN.
           CALL 'CUSTPROG' USING SOME-RECORD
           STOP RUN.
"""


def test_call_statements_found() -> None:
    result = parse_cobol(CALL_SNIPPET)
    progs = [p for p, _ in result.call_statements]
    assert "CUSTPROG" in progs


# ---------------------------------------------------------------------------
# FILE SELECT / ASSIGN
# ---------------------------------------------------------------------------


SELECT_SNIPPET = """\
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE ASSIGN TO CUSTMAST
               ORGANIZATION IS SEQUENTIAL.
"""


def test_file_select_found() -> None:
    result = parse_cobol(SELECT_SNIPPET)
    assert len(result.file_selects) == 1
    sel = result.file_selects[0]
    assert sel.logical_name == "CUSTOMER-FILE"
    assert sel.assign_to == "CUSTMAST"


# ---------------------------------------------------------------------------
# Local declaration detection (planted failure pattern)
# ---------------------------------------------------------------------------


LOCAL_DECL_SNIPPET = """\
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-ACCT-CUST-ID             PIC X(8).
       01  WS-SOME-OTHER-FIELD         PIC X(20).
"""


def test_local_declaration_detected() -> None:
    result = parse_cobol(LOCAL_DECL_SNIPPET)
    names = [f.name for f in result.local_declarations]
    assert "WS-ACCT-CUST-ID" in names


# ---------------------------------------------------------------------------
# DATA DIVISION field extraction
# ---------------------------------------------------------------------------


FIELDS_SNIPPET = """\
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CUSTOMER-MASTER-RECORD.
           05  CUSTOMER-ID             PIC X(8).
           05  CUSTOMER-NAME           PIC X(30).
"""


def test_data_fields_extracted() -> None:
    result = parse_cobol(FIELDS_SNIPPET)
    names = [f.name for f in result.fields]
    assert "CUSTOMER-ID" in names
    assert "CUSTOMER-NAME" in names


def test_field_byte_size() -> None:
    result = parse_cobol(FIELDS_SNIPPET)
    cid = next(f for f in result.fields if f.name == "CUSTOMER-ID")
    assert cid.byte_size == 8
