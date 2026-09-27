"""AFP structural parser for synthetic mainframe print documents.

Parses MO:DCA (Mixed Object Document Content Architecture) structured fields
specifically for the synthetic CUSTRPT.AFP document.
This is structural analysis and deterministic visualization, NOT full IBM AFP/PSF emulation.
"""

from __future__ import annotations

import re
from pathlib import Path

from zforge.afp.models import (
    AFPDocument,
    AFPElement,
    AFPElementType,
    AFPPage,
)

# Known MO:DCA Structured Field Triplet Identifiers
_ID_BDT = bytes([0xD3, 0xA8, 0xA8])  # Begin Document
_ID_BPG = bytes([0xD3, 0xA8, 0xAF])  # Begin Page
_ID_BPT = bytes([0xD3, 0xA8, 0xBB])  # Begin Presentation Text
_ID_PTX = bytes([0xD3, 0xEE, 0xBB])  # Presentation Text Data
_ID_EPT = bytes([0xD3, 0xA9, 0xBB])  # End Presentation Text
_ID_EPG = bytes([0xD3, 0xA9, 0xAF])  # End Page
_ID_EDT = bytes([0xD3, 0xA9, 0xA8])  # End Document


def parse_afp_bytes(
    data: bytes,
    file_name: str = "CUSTRPT.AFP",
    filename: str | None = None,
) -> AFPDocument:
    """Parse raw bytes of a synthetic AFP file into an AFPDocument."""
    if filename is not None:
        file_name = filename
    offset = 0
    sf_count = 0

    doc_name = file_name
    pages: list[AFPPage] = []
    current_page: AFPPage | None = None
    y_cursor = 140

    while offset + 6 <= len(data):
        rec_len = int.from_bytes(data[offset : offset + 2], "big")
        if rec_len < 6 or offset + rec_len > len(data):
            break

        sf_type = data[offset + 3 : offset + 6]
        payload = data[offset + 6 : offset + rec_len]
        sf_count += 1

        if sf_type == _ID_BDT:
            doc_name = payload.decode("ascii", errors="replace").strip() or "CUSTRPT-DOC"

        elif sf_type == _ID_BPG:
            decoded_page = payload.decode("ascii", errors="replace").strip()
            page_name = decoded_page or f"PAGE{len(pages)+1:03d}"
            current_page = AFPPage(page_number=len(pages) + 1, page_name=page_name, elements=[])
            pages.append(current_page)
            # Add page title banner
            current_page.elements.append(
                AFPElement(
                    type=AFPElementType.TITLE,
                    text="ZENITH BANK CUSTOMER STATEMENT",
                    x=200,
                    y=70,
                )
            )

        elif sf_type == _ID_PTX and current_page is not None:
            text = payload.decode("latin1", errors="replace")

            # Parse "CUSTOMER-ID: <val>  <header>"
            cid_match = re.search(r"CUSTOMER-ID:\s*([A-Za-z0-9]+)", text)
            if cid_match:
                cid_val = cid_match.group(1).strip()
                current_page.elements.append(
                    AFPElement(
                        type=AFPElementType.FIELD_LABEL,
                        text="Customer ID:",
                        x=80,
                        y=y_cursor,
                    )
                )
                current_page.elements.append(
                    AFPElement(
                        type=AFPElementType.FIELD_VALUE,
                        text=cid_val,
                        x=220,
                        y=y_cursor,
                        field_name="CUSTOMER-ID",
                        field_value=cid_val,
                        inferred_length=len(cid_val),
                    )
                )
                y_cursor += 35

            # Parse "NAME: <val>"
            name_match = re.search(r"NAME:\s*([A-Za-z0-9\s]+)", text)
            if name_match:
                name_val = name_match.group(1).strip()
                current_page.elements.append(
                    AFPElement(
                        type=AFPElementType.FIELD_LABEL,
                        text="Customer Name:",
                        x=80,
                        y=y_cursor,
                    )
                )
                current_page.elements.append(
                    AFPElement(
                        type=AFPElementType.FIELD_VALUE,
                        text=name_val,
                        x=220,
                        y=y_cursor,
                        field_name="CUSTOMER-NAME",
                        field_value=name_val,
                        inferred_length=len(name_val),
                    )
                )
                y_cursor += 35

        elif sf_type == _ID_EPG:
            current_page = None

        offset += rec_len

    return AFPDocument(
        document_name=doc_name,
        file_name=file_name,
        pages=pages,
        structured_fields_count=sf_count,
        raw_byte_size=len(data),
    )


def parse_afp_file(file_path: Path | str) -> AFPDocument:
    """Read and parse an AFP file from disk."""
    path = Path(file_path).resolve()
    data = path.read_bytes()
    return parse_afp_bytes(data, file_name=path.name)
