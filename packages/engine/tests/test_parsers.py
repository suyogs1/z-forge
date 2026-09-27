"""Unit tests for copybook, HLASM, JCL, and dataset parsers."""

from __future__ import annotations

from zforge.ingestion.copybook_parser import parse_copybook
from zforge.ingestion.dataset_parser import parse_dsd
from zforge.ingestion.hlasm_parser import parse_hlasm
from zforge.ingestion.jcl_parser import parse_jcl

# ---------------------------------------------------------------------------
# Copybook parser
# ---------------------------------------------------------------------------

CUSTMAST_CONTENT = """\
       01  CUSTOMER-MASTER-RECORD.
           05  CUSTOMER-ID             PIC X(8).
           05  CUSTOMER-NAME           PIC X(30).
           05  CUSTOMER-STATUS         PIC X.
               88  CUST-ACTIVE         VALUE 'A'.
"""

ACCTMAST_CONTENT = """\
       01  ACCOUNT-MASTER-RECORD.
           05  ACCOUNT-NUMBER          PIC X(10).
               COPY CUSTMAST.
"""


def test_copybook_fields_extracted() -> None:
    result = parse_copybook(CUSTMAST_CONTENT, name="CUSTMAST")
    names = [f.name for f in result.fields if f.pic]
    assert "CUSTOMER-ID" in names
    assert "CUSTOMER-NAME" in names


def test_copybook_byte_sizes() -> None:
    result = parse_copybook(CUSTMAST_CONTENT, name="CUSTMAST")
    cid = next(f for f in result.fields if f.name == "CUSTOMER-ID")
    assert cid.byte_size == 8


def test_copybook_copy_statements() -> None:
    result = parse_copybook(ACCTMAST_CONTENT, name="ACCTMAST")
    names = [c for c, _ in result.copy_statements]
    assert "CUSTMAST" in names


# ---------------------------------------------------------------------------
# HLASM parser
# ---------------------------------------------------------------------------

CUSTDSCT_CONTENT = """\
CUSTMREC DSECT
CUSTID   DS    CL8             Customer ID
CUSTNAME DS    CL30            Customer name
CUSTLEN  EQU   *-CUSTMREC
CUSTIDLN EQU   8
         END
"""


def test_hlasm_dsect_detected() -> None:
    result = parse_hlasm(CUSTDSCT_CONTENT)
    assert len(result.sections) == 1
    assert result.sections[0].kind == "DSECT"
    assert result.sections[0].name == "CUSTMREC"


def test_hlasm_fields_extracted() -> None:
    result = parse_hlasm(CUSTDSCT_CONTENT)
    sect = result.sections[0]
    labels = [f.label for f in sect.fields if f.opcode == "DS"]
    assert "CUSTID" in labels
    assert "CUSTNAME" in labels


def test_hlasm_field_offsets() -> None:
    result = parse_hlasm(CUSTDSCT_CONTENT)
    sect = result.sections[0]
    custid = next(f for f in sect.fields if f.label == "CUSTID")
    custname = next(f for f in sect.fields if f.label == "CUSTNAME")
    assert custid.offset == 0
    assert custid.byte_size == 8
    assert custname.offset == 8
    assert custname.byte_size == 30


def test_hlasm_equ_symbols() -> None:
    result = parse_hlasm(CUSTDSCT_CONTENT)
    assert result.equ_symbols.get("CUSTIDLN") == 8


# ---------------------------------------------------------------------------
# JCL parser
# ---------------------------------------------------------------------------

NIGHTLY_JCL = """\
//NIGHTLY  JOB (ZENITH),'NIGHTLY BATCH'
//*
//STEP010  EXEC PGM=CUSTPROG
//CUSTMAST DD  DSN=ZENITH.CUST.MASTER.FILE,DISP=SHR,
//             DCB=(RECFM=FB,LRECL=80,BLKSIZE=3200)
//STEP020  EXEC PGM=ACCTPROG
//ACCTMAST DD  DSN=ZENITH.ACCT.MASTER.FILE,DISP=SHR,
//             DCB=(RECFM=FB,LRECL=80,BLKSIZE=3200)
//STEP030  EXEC PGM=CUSTRPT
//CUSTMAST DD  DSN=ZENITH.CUST.MASTER.FILE,DISP=SHR
//CUSTRPT  DD  DSN=ZENITH.CUST.REPORT.FILE,
//             DISP=(NEW,CATLG,DELETE)
"""


def test_jcl_job_name() -> None:
    result = parse_jcl(NIGHTLY_JCL)
    assert result.job_name == "NIGHTLY"


def test_jcl_steps_found() -> None:
    result = parse_jcl(NIGHTLY_JCL)
    pgms = [s.pgm for s in result.steps]
    assert "CUSTPROG" in pgms
    assert "ACCTPROG" in pgms
    assert "CUSTRPT" in pgms


def test_jcl_dd_dsn_extracted() -> None:
    result = parse_jcl(NIGHTLY_JCL)
    all_dsns = [dd.dsn for dd in result.all_dds if dd.dsn]
    assert "ZENITH.CUST.MASTER.FILE" in all_dsns


def test_jcl_dataset_producers() -> None:
    result = parse_jcl(NIGHTLY_JCL)
    producers = result.dataset_producers()
    # CUSTRPT writes CUST.REPORT.FILE
    prod_pairs = [(p, d) for p, d in producers]
    assert any("CUSTRPT" in p and "REPORT" in d for p, d in prod_pairs)


def test_jcl_dataset_consumers() -> None:
    result = parse_jcl(NIGHTLY_JCL)
    consumers = result.dataset_consumers()
    # CUSTPROG reads CUST.MASTER.FILE
    assert any("CUSTPROG" in p and "MASTER" in d for p, d in consumers)


# ---------------------------------------------------------------------------
# Dataset parser
# ---------------------------------------------------------------------------

DSD_CONTENT = """\
{
  "dataset_name": "ZENITH.CUST.MASTER.FILE",
  "record_name": "CUSTOMER-MASTER-RECORD",
  "copybook": "CUSTMAST.CPY",
  "dcb": {"recfm": "FB", "lrecl": 80, "blksize": 3200},
  "fields": [
    {"name": "CUSTOMER-ID", "type": "X", "length": 8, "offset": 0, "pic": "PIC X(8)"},
    {"name": "CUSTOMER-NAME", "type": "X", "length": 30, "offset": 8, "pic": "PIC X(30)"}
  ]
}
"""


def test_dsd_dataset_name() -> None:
    result = parse_dsd(DSD_CONTENT)
    assert result.dataset_name == "ZENITH.CUST.MASTER.FILE"


def test_dsd_fields_extracted() -> None:
    result = parse_dsd(DSD_CONTENT)
    names = [f.name for f in result.fields]
    assert "CUSTOMER-ID" in names
    assert "CUSTOMER-NAME" in names


def test_dsd_lrecl() -> None:
    result = parse_dsd(DSD_CONTENT)
    assert result.dcb.lrecl == 80


def test_dsd_field_offset_and_length() -> None:
    result = parse_dsd(DSD_CONTENT)
    cid = next(f for f in result.fields if f.name == "CUSTOMER-ID")
    assert cid.offset == 0
    assert cid.length == 8
