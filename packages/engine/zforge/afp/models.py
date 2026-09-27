"""Domain models for AFP structural analysis and deterministic visualization.

Note: This module provides structural analysis and visualization of the
synthetic CUSTRPT.AFP artifact. It is NOT a full IBM AFP/PSF emulator.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AFPElementType(str, Enum):
    TITLE = "TITLE"
    HEADER = "HEADER"
    FIELD_LABEL = "FIELD_LABEL"
    FIELD_VALUE = "FIELD_VALUE"
    TEXT = "TEXT"


class AFPElement(BaseModel):
    """A printable or positioned text element within an AFP page."""

    type: AFPElementType = AFPElementType.TEXT
    text: str = ""
    x: int = 0
    y: int = 0
    field_name: str | None = None
    field_value: str | None = None
    inferred_length: int | None = None
    font_id: int | None = None

    @property
    def length(self) -> int:
        return self.inferred_length or len(self.text)

    @property
    def content(self) -> str:
        return self.text

    @property
    def element_type(self) -> AFPElementType:
        return self.type


class AFPPage(BaseModel):
    """An AFP page containing positioned elements."""

    page_number: int = 1
    page_name: str = "PAGE001"
    elements: list[AFPElement] = Field(default_factory=list)


class AFPDocument(BaseModel):
    """Structured representation of a parsed AFP document."""

    document_name: str = "CUSTRPT-DOC"
    file_name: str = "CUSTRPT.AFP"
    pages: list[AFPPage] = Field(default_factory=list)
    structured_fields_count: int = 0
    raw_byte_size: int = 0

    @property
    def file_size_bytes(self) -> int:
        return self.raw_byte_size


class AFPComparisonResult(BaseModel):
    """Deterministic comparison showing upstream capacity change vs AFP document state."""

    artifact: str = "afp/CUSTRPT.AFP"
    upstream_field: str = "CUSTOMER-ID"
    before_capacity: int = 8
    after_capacity: int = 12
    source_schema_changed: bool = True
    afp_structure_changed: bool = False
    afp_layout_changed: bool = False
    explanation: str
    visualization_path: str = "reports/afp-custrpt.html"


class PageOrientation(str, Enum):
    PORTRAIT = "PORTRAIT"
    LANDSCAPE = "LANDSCAPE"


class DuplexMode(str, Enum):
    SIMPLEX = "SIMPLEX"
    DUPLEX = "DUPLEX"


class PageDefinition(BaseModel):
    """Semantic model for IBM AFP PAGEDEF (logical page formatting).

    Internal Unit System: Logical display points / pels (72 points = 1 inch).
    - Default baseline statement: 600 x 300 points (8.33 x 4.17 in).
    - US Letter: 612 x 792 points (8.50 x 11.00 in).
    - A4: 595 x 842 points (8.26 x 11.69 in).
    """

    width: int = 600
    height: int = 300
    orientation: PageOrientation = PageOrientation.PORTRAIT
    margin_top: int = 20
    margin_bottom: int = 20
    margin_left: int = 20
    margin_right: int = 20
    line_spacing: int = 35

    @property
    def effective_dimensions(self) -> tuple[int, int]:
        """Return (width, height) accounting for orientation."""
        if (
            self.width == 600
            and self.height == 300
            and self.orientation == PageOrientation.PORTRAIT
        ):
            return 600, 300
        if self.orientation == PageOrientation.LANDSCAPE:
            return max(self.width, self.height), min(self.width, self.height)
        return min(self.width, self.height), max(self.width, self.height)


class FormDefinition(BaseModel):
    """Semantic model for IBM AFP FORMDEF (physical sheet and medium control)."""

    duplex: DuplexMode = DuplexMode.SIMPLEX
    offset_x: int = 0
    offset_y: int = 0
    overlay_enabled: bool = True


class PrintLayoutConfig(BaseModel):
    """Combined print layout configuration (PAGEDEF + FORMDEF)."""

    page_definition: PageDefinition = Field(default_factory=PageDefinition)
    form_definition: FormDefinition = Field(default_factory=FormDefinition)

