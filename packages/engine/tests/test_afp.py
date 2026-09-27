"""Tests for synthetic AFP structural analysis and deterministic visualization.

Validates:
1. AFP structural parser
2. AFP semantic representation
3. Deterministic rendering (SVG and HTML)
4. Before/After capacity comparison (truthful, non-emulated)
5. AFP evidence and lineage integration
6. Repeated deterministic rendering
"""

from __future__ import annotations

from pathlib import Path

from zforge.afp.comparison import compare_afp_capacity
from zforge.afp.impact import get_afp_lineage_impact
from zforge.afp.models import (
    AFPComparisonResult,
    AFPDocument,
    AFPElement,
    AFPElementType,
    AFPPage,
    DuplexMode,
    FormDefinition,
    PageDefinition,
    PageOrientation,
    PrintLayoutConfig,
)
from zforge.afp.parser import parse_afp_bytes, parse_afp_file
from zforge.afp.renderer import (
    generate_ppfa_source,
    render_afp_html,
    render_afp_svg,
    save_afp_visualization,
)
from zforge.models import ChangeRequest, ChangeSet
from zforge.report.evidence import generate_tamper_evident_report

_WORKSPACE = Path(__file__).parents[3] / "workspace" / "synthetic-banking"
_AFP_FILE = _WORKSPACE / "afp" / "CUSTRPT.AFP"


def test_afp_file_exists() -> None:
    """Ensure the synthetic AFP file is present and non-empty."""
    assert _AFP_FILE.exists(), f"Missing synthetic AFP artifact at {_AFP_FILE}"
    assert _AFP_FILE.stat().st_size > 0


def test_afp_parser_synthetic_document() -> None:
    """Task 1: Test parsing the actual synthetic CUSTRPT.AFP artifact."""
    doc = parse_afp_file(_AFP_FILE)
    assert isinstance(doc, AFPDocument)
    assert doc.document_name == "CUSTRPT-DOC"
    assert doc.file_name == "CUSTRPT.AFP"
    assert doc.raw_byte_size == 156
    assert doc.file_size_bytes == 156
    assert len(doc.pages) == 1

    page = doc.pages[0]
    assert isinstance(page, AFPPage)
    assert page.page_number == 1
    assert page.page_name == "PAGE001"
    assert len(page.elements) == 5

    # Check title element
    title_elem = page.elements[0]
    assert title_elem.type == AFPElementType.TITLE
    assert title_elem.text == "ZENITH BANK CUSTOMER STATEMENT"

    # Check Customer ID elements
    cid_label = page.elements[1]
    assert cid_label.type == AFPElementType.FIELD_LABEL
    assert cid_label.text == "Customer ID:"

    cid_val = page.elements[2]
    assert cid_val.type == AFPElementType.FIELD_VALUE
    assert cid_val.field_name == "CUSTOMER-ID"
    assert cid_val.field_value == "ZB000001"
    assert cid_val.inferred_length == 8

    # Check Name elements
    name_label = page.elements[3]
    assert name_label.type == AFPElementType.FIELD_LABEL
    assert name_label.text == "Customer Name:"

    name_val = page.elements[4]
    assert name_val.type == AFPElementType.FIELD_VALUE
    assert name_val.field_name == "CUSTOMER-NAME"
    assert name_val.field_value == "ALDRIDGE SIMONE J"
    assert name_val.inferred_length == 17


def test_afp_parser_empty_or_invalid_bytes() -> None:
    """Test parser behavior on empty or corrupt bytes."""
    doc_empty = parse_afp_bytes(b"", filename="empty.afp")
    assert doc_empty.document_name == "empty.afp"
    assert len(doc_empty.pages) == 0

    doc_corrupt = parse_afp_bytes(b"\x00\x05\x00\xd3\xa8", filename="corrupt.afp")
    assert doc_corrupt.document_name == "corrupt.afp"
    assert len(doc_corrupt.pages) == 0


def test_afp_semantic_model() -> None:
    """Task 2: Test the AFP semantic model classes and serialization."""
    elem = AFPElement(
        type=AFPElementType.TEXT,
        text="TEST DATA",
        x=50,
        y=100,
        inferred_length=9,
        font_id=1,
    )
    page = AFPPage(page_number=1, page_name="P1", elements=[elem])
    doc = AFPDocument(
        document_name="TESTDOC",
        raw_byte_size=100,
        pages=[page],
    )

    dumped = doc.model_dump()
    assert dumped["document_name"] == "TESTDOC"
    assert len(dumped["pages"]) == 1
    assert dumped["pages"][0]["elements"][0]["text"] == "TEST DATA"
    assert dumped["pages"][0]["elements"][0]["x"] == 50

    # Roundtrip check
    restored = AFPDocument.model_validate(dumped)
    assert restored.document_name == doc.document_name
    assert len(restored.pages) == 1
    assert restored.pages[0].elements[0].length == 9
    assert restored.file_size_bytes == 100


def test_afp_deterministic_rendering_svg() -> None:
    """Task 3: Test SVG rendering contains proper styling and layout."""
    doc = parse_afp_file(_AFP_FILE)
    svg = render_afp_svg(doc)

    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert 'viewBox="0 0 600 300"' in svg
    assert "ZENITH BANK CUSTOMER STATEMENT" in svg
    assert "Customer ID:" in svg
    assert "ZB000001" in svg
    assert "Customer Name:" in svg
    assert "ALDRIDGE SIMONE J" in svg


def test_afp_deterministic_rendering_html(tmp_path: Path) -> None:
    """Task 3: Test HTML rendering with embedded SVG and comparison table."""
    doc = parse_afp_file(_AFP_FILE)
    req = ChangeRequest(
        field_name="CUSTOMER-ID",
        target_type="PIC X(12)",
        old_length=8,
        new_length=12,
        description="Expand CUSTOMER-ID",
    )
    comp = compare_afp_capacity(doc, req)
    html = render_afp_html(doc, comparison=comp)

    assert "<!DOCTYPE html>" in html
    assert "Z-FORGE — AFP Output Visualization" in html
    assert "<svg" in html
    assert "Schema Impact Comparison" in html
    assert "X(8)" in html
    assert "X(12)" in html
    assert "CUSTRPT-DOC" in html
    assert "ZB000001" in html

    # Test saving
    out_file = tmp_path / "afp-test.html"
    save_afp_visualization(doc, out_file, comparison=comp)
    assert out_file.exists()
    assert out_file.read_text(encoding="utf-8") == html


def test_afp_before_after_comparison() -> None:
    """Task 4: Test before/after comparison distinguishes schema vs layout changes."""
    doc = parse_afp_file(_AFP_FILE)
    req = ChangeRequest(
        field_name="CUSTOMER-ID",
        target_type="PIC X(12)",
        old_length=8,
        new_length=12,
        description="Expand CUSTOMER-ID",
    )
    comp = compare_afp_capacity(doc, req)

    assert isinstance(comp, AFPComparisonResult)
    # Upstream schema changed from 8 to 12
    assert comp.source_schema_changed is True
    assert comp.before_capacity == 8
    assert comp.after_capacity == 12

    # Static binary layout did NOT change without recompilation
    assert comp.afp_structure_changed is False
    assert comp.afp_layout_changed is False
    assert "CUSTRPT.AFP" in comp.explanation
    assert "re-executed" in comp.explanation

    # Test when schema is unchanged
    req_same = ChangeRequest(
        field_name="CUSTOMER-ID",
        target_type="PIC X(8)",
        old_length=8,
        new_length=8,
    )
    comp_same = compare_afp_capacity(doc, req_same)
    assert comp_same.source_schema_changed is False


def test_afp_impact_lineage_helper() -> None:
    """Task 5: Test AFP downstream lineage metadata helper."""
    info = get_afp_lineage_impact()
    assert info["artifact_id"] == "afp/CUSTRPT.AFP"
    assert info["artifact_type"] == "AFP"
    expected_path = [
        "CUSTOMER-ID",
        "copybooks/CUSTMAST.CPY",
        "cobol/CUSTRPT.CBL",
        "datasets/CUST.REPORT.FILE.dsd",
        "jcl/CUSTRPT.JCL",
        "afp/CUSTRPT.AFP",
    ]
    assert info["lineage_path"] == expected_path


def test_afp_evidence_integration() -> None:
    """Task 6: Test evidence report includes AFP impact deterministically."""
    doc = parse_afp_file(_AFP_FILE)
    req = ChangeRequest(
        field_name="CUSTOMER-ID",
        target_type="PIC X(12)",
        old_length=8,
        new_length=12,
    )
    comp = compare_afp_capacity(doc, req)
    afp_impact = {
        "artifact": "afp/CUSTRPT.AFP",
        "document_name": doc.document_name,
        "pages_count": len(doc.pages),
        "total_elements": sum(len(p.elements) for p in doc.pages),
        "lineage_path": get_afp_lineage_impact()["lineage_path"],
        "comparison": comp.model_dump(),
        "visualization_path": "reports/afp-custrpt.html",
    }

    report = generate_tamper_evident_report(
        workspace_root=_WORKSPACE,
        request=req,
        impacted_artifacts=[],
        proposals=ChangeSet(id="cs-test", proposals=[], ordered_artifact_ids=[]),
        snapshot_ids=[],
        scenarios=[],
        failures=[],
        adversarial_findings=[],
        final_status="PASS",
        afp_impact=afp_impact,
    )

    assert report.afp_impact is not None
    assert report.afp_impact["artifact"] == "afp/CUSTRPT.AFP"
    assert report.afp_impact["document_name"] == "CUSTRPT-DOC"
    assert report.afp_impact["comparison"]["source_schema_changed"] is True
    assert "report_sha256" in report.deterministic_hashes


def test_afp_repeated_rendering_determinism() -> None:
    """Task 7: Test that repeated rendering produces byte-identical output."""
    doc = parse_afp_file(_AFP_FILE)
    req = ChangeRequest(
        field_name="CUSTOMER-ID",
        target_type="PIC X(12)",
        old_length=8,
        new_length=12,
    )
    comp = compare_afp_capacity(doc, req)

    svg1 = render_afp_svg(doc)
    svg2 = render_afp_svg(doc)
    assert svg1 == svg2

    html1 = render_afp_html(doc, comparison=comp)
    html2 = render_afp_html(doc, comparison=comp)
    assert html1 == html2


def test_afp_default_renderer_backward_compatible() -> None:
    """Verify default renderer without config preserves 600x300 and baseline layout."""
    doc = parse_afp_file(_AFP_FILE)
    svg_default = render_afp_svg(doc)
    svg_explicit_none = render_afp_svg(doc, None)
    svg_default_cfg = render_afp_svg(doc, PrintLayoutConfig())

    assert svg_default == svg_explicit_none == svg_default_cfg
    assert 'viewBox="0 0 600 300"' in svg_default
    assert 'rect x="20" y="20" width="560" height="260"' in svg_default
    assert "ZENITH BANK CUSTOMER STATEMENT" in svg_default


def test_afp_custom_pagedef_changes_svg_dimensions() -> None:
    """Task 9: Verify custom PageDefinition modifies SVG width and height."""
    doc = parse_afp_file(_AFP_FILE)
    cfg = PrintLayoutConfig(
        page_definition=PageDefinition(width=850, height=500, orientation=PageOrientation.PORTRAIT)
    )
    svg = render_afp_svg(doc, cfg)
    assert 'viewBox="0 0 500 850"' in svg or 'viewBox="0 0 850 500"' in svg
    assert 'width="850"' in svg or 'width="500"' in svg


def test_afp_orientation_changes_rendered_dimensions() -> None:
    """Task 9: Verify orientation changes rendered dimensions."""
    pdef_portrait = PageDefinition(width=595, height=842, orientation=PageOrientation.PORTRAIT)
    pdef_landscape = PageDefinition(width=595, height=842, orientation=PageOrientation.LANDSCAPE)

    assert pdef_portrait.effective_dimensions == (595, 842)
    assert pdef_landscape.effective_dimensions == (842, 595)

    doc = parse_afp_file(_AFP_FILE)
    svg_p = render_afp_svg(doc, PrintLayoutConfig(page_definition=pdef_portrait))
    svg_l = render_afp_svg(doc, PrintLayoutConfig(page_definition=pdef_landscape))

    assert 'viewBox="0 0 595 842"' in svg_p
    assert 'viewBox="0 0 842 595"' in svg_l


def test_afp_margins_affect_printable_area() -> None:
    """Task 9: Verify margins affect printable area and text offset."""
    doc = parse_afp_file(_AFP_FILE)
    cfg = PrintLayoutConfig(
        page_definition=PageDefinition(
            width=600,
            height=300,
            margin_left=50,
            margin_right=50,
            margin_top=40,
            margin_bottom=40,
        )
    )
    svg = render_afp_svg(doc, cfg)
    # Printable width: 600 - 50 - 50 = 500, height: 300 - 40 - 40 = 220
    assert 'x="50" y="40" width="500" height="220"' in svg


def test_afp_formdef_changes_form_behavior() -> None:
    """Task 9: Verify FormDefinition modifies duplex badge and overlay header line."""
    doc = parse_afp_file(_AFP_FILE)

    # Duplex mode
    cfg_duplex = PrintLayoutConfig(form_definition=FormDefinition(duplex=DuplexMode.DUPLEX))
    svg_duplex = render_afp_svg(doc, cfg_duplex)
    assert "DUPLEX" in svg_duplex

    # Overlay disabled
    cfg_no_overlay = PrintLayoutConfig(form_definition=FormDefinition(overlay_enabled=False))
    svg_no_overlay = render_afp_svg(doc, cfg_no_overlay)
    assert 'stroke="#cbd5e1" stroke-width="1"' not in svg_no_overlay


def test_afp_ppfa_source_generation_deterministic() -> None:
    """Task 9: Verify PPFA source generation contains valid syntax and is deterministic."""
    cfg = PrintLayoutConfig(
        page_definition=PageDefinition(width=612, height=792, line_spacing=40),
        form_definition=FormDefinition(duplex=DuplexMode.DUPLEX, offset_x=10, offset_y=15),
    )
    ppfa1 = generate_ppfa_source(cfg)
    ppfa2 = generate_ppfa_source(cfg)

    assert ppfa1 == ppfa2
    assert "FORMDEF F1CUST" in ppfa1
    assert "PAGEDEF P1CUST" in ppfa1
    assert "DUPLEX NORMAL;" in ppfa1
    assert "LINESP 40 POINTS;" in ppfa1
    assert "Generated PPFA Source — semantic export" in ppfa1
    assert "not compiled by IBM PPFA" in ppfa1


def test_afp_json_configuration_generation_deterministic() -> None:
    """Task 9: Verify PrintLayoutConfig JSON serialization is deterministic."""
    cfg = PrintLayoutConfig()
    json1 = cfg.model_dump_json(indent=2)
    json2 = cfg.model_dump_json(indent=2)

    assert json1 == json2
    assert "page_definition" in json1
    assert "form_definition" in json1
    assert '"width": 600' in json1


def test_afp_save_visualization_exports_all_artifacts(tmp_path: Path) -> None:
    """Verify save_afp_visualization exports HTML, SVG, PPFA source, and layout JSON."""
    doc = parse_afp_file(_AFP_FILE)
    out_html = tmp_path / "reports" / "afp-custrpt.html"
    saved_path = save_afp_visualization(doc, out_html)

    assert saved_path == out_html
    assert out_html.exists()
    assert (tmp_path / "reports" / "afp-custrpt.svg").exists()
    assert (tmp_path / "reports" / "CUSTRPT.ppfa").exists()
    assert (tmp_path / "reports" / "CUSTRPT-print-layout.json").exists()

    ppfa_text = (tmp_path / "reports" / "CUSTRPT.ppfa").read_text(encoding="utf-8")
    assert "FORMDEF F1CUST" in ppfa_text
    assert "PAGEDEF P1CUST" in ppfa_text

