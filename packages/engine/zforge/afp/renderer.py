"""Deterministic text and HTML/SVG layout renderer for synthetic AFP documents.

Renders an interactive business customer report based on parsed AFP MO:DCA elements,
semantic PAGEDEF/FORMDEF models, and generates IBM PPFA source code.
"""

from __future__ import annotations

from pathlib import Path

from zforge.afp.models import (
    AFPComparisonResult,
    AFPDocument,
    DuplexMode,
    PageOrientation,
    PrintLayoutConfig,
)


def generate_ppfa_source(config: PrintLayoutConfig) -> str:
    """Generate human-readable IBM PPFA-style source text for the layout config.

    Note: This is a semantic PPFA source export; it is NOT compiled or validated by IBM PPFA.
    """
    pdef = config.page_definition
    fdef = config.form_definition
    page_w, page_h = pdef.effective_dimensions

    # Convert internal points to inches (72 points = 1 inch)
    width_in = page_w / 72.0
    height_in = page_h / 72.0
    margin_l_in = pdef.margin_left / 72.0
    margin_t_in = pdef.margin_top / 72.0
    margin_r_in = pdef.margin_right / 72.0
    margin_b_in = pdef.margin_bottom / 72.0
    offset_x_in = fdef.offset_x / 72.0
    offset_y_in = fdef.offset_y / 72.0

    duplex_kw = "NORMAL" if fdef.duplex == DuplexMode.DUPLEX else "NO"
    direction_kw = "ACROSS" if pdef.orientation == PageOrientation.LANDSCAPE else "DOWN"

    return f"""/* ============================================================ */
/* Generated PPFA Source — semantic export                      */
/* Z-FORGE IBM Z Print Engineering                              */
/* Note: Semantic export; not compiled by IBM PPFA.            */
/* ============================================================ */

FORMDEF F1CUST
    OFFSET {offset_x_in:.2f} IN {offset_y_in:.2f} IN
    DUPLEX {duplex_kw};

PAGEDEF P1CUST
    WIDTH {width_in:.2f} IN
    HEIGHT {height_in:.2f} IN
    DIRECTION {direction_kw}
    MARGINS {margin_l_in:.2f} IN {margin_t_in:.2f} IN {margin_r_in:.2f} IN {margin_b_in:.2f} IN;

    SETUNITS LINESP {pdef.line_spacing} POINTS;
    FONT FNT1 'C0S0PR10';

    PRINTLINE CHANNEL 1 POSITION MARGIN 1.0 IN FONT FNT1;
    PRINTLINE POSITION MARGIN NEXT FONT FNT1;

/* PPFA END */"""


def render_afp_svg(doc: AFPDocument, config: PrintLayoutConfig | None = None) -> str:
    """Generate deterministic SVG representing the printed AFP report page."""
    cfg = config if config is not None else PrintLayoutConfig()
    pdef = cfg.page_definition
    fdef = cfg.form_definition

    page_w, page_h = pdef.effective_dimensions
    print_x = fdef.offset_x + pdef.margin_left
    print_y = fdef.offset_y + pdef.margin_top
    print_w = max(0, page_w - pdef.margin_left - pdef.margin_right)
    print_h = max(0, page_h - pdef.margin_top - pdef.margin_bottom)

    # Calculate coordinate offsets from default baseline (margin_left=20, margin_top=20)
    delta_x = print_x - 20
    delta_y = print_y - 20

    elements_svg: list[str] = []
    if doc.pages:
        page = doc.pages[0]
        y_val_cursor = 140 + delta_y
        for elem in page.elements:
            if elem.type.value == "TITLE":
                elem_x = elem.x + delta_x
                elem_y = elem.y + delta_y
                elements_svg.append(
                    f'    <text x="{elem_x}" y="{elem_y}" font-family="monospace" font-size="16" '
                    f'font-weight="bold" fill="#0f172a">{elem.text}</text>'
                )
            elif elem.type.value == "FIELD_LABEL":
                elem_x = elem.x + delta_x
                elements_svg.append(
                    f'    <text x="{elem_x}" y="{y_val_cursor}" font-family="monospace" '
                    f'font-size="13" font-weight="600" fill="#475569">{elem.text}</text>'
                )
            elif elem.type.value == "FIELD_VALUE":
                elem_x = elem.x + delta_x
                elements_svg.append(
                    f'    <text x="{elem_x}" y="{y_val_cursor}" font-family="monospace" '
                    f'font-size="13" font-weight="bold" fill="#1e293b">{elem.text}</text>'
                )
                y_val_cursor += pdef.line_spacing

    overlay_line = ""
    if fdef.overlay_enabled:
        line_x1 = print_x
        line_x2 = print_x + print_w
        line_y = print_y + 75
        overlay_line = (
            f'  <line x1="{line_x1}" y1="{line_y}" x2="{line_x2}" y2="{line_y}" '
            f'stroke="#cbd5e1" stroke-width="1"/>\n'
        )

    duplex_badge = ""
    if fdef.duplex == DuplexMode.DUPLEX:
        duplex_badge = (
            f'  <rect x="{page_w - 95}" y="{page_h - 26}" width="75" height="18" '
            f'fill="#e2e8f0" rx="3"/>\n'
            f'  <text x="{page_w - 85}" y="{page_h - 13}" font-family="monospace" '
            f'font-size="10" font-weight="bold" fill="#475569">DUPLEX</text>\n'
        )

    svg_content = "\n".join(elements_svg)
    return f"""<svg width="{page_w}" height="{page_h}" viewBox="0 0 {page_w} {page_h}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{page_w}" height="{page_h}" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2" rx="6"/>
  <rect x="{print_x}" y="{print_y}" width="{print_w}" height="{print_h}"
        fill="#ffffff" stroke="#e2e8f0" stroke-width="1" rx="4"/>
{overlay_line}{duplex_badge}{svg_content}
</svg>"""


def render_afp_html(
    doc: AFPDocument,
    comparison: AFPComparisonResult | None = None,
    config: PrintLayoutConfig | None = None,
) -> str:
    """Generate deterministic interactive HTML report editor with live SVG and PPFA export."""
    cfg = config if config is not None else PrintLayoutConfig()
    pdef = cfg.page_definition
    fdef = cfg.form_definition

    svg_markup = render_afp_svg(doc, cfg)
    ppfa_markup = generate_ppfa_source(cfg)

    comp_section = ""
    if comparison:
        comp_section = f"""
    <div class="comparison-card">
      <h3>Schema Impact Comparison (CUSTOMER-ID)</h3>
      <div class="grid">
        <div class="box">
          <h4>BEFORE CHANGE</h4>
          <p><strong>Field Capacity:</strong> X({comparison.before_capacity}) (8 bytes)</p>
          <p><strong>AFP Record Value:</strong> <code>ZB000001</code></p>
          <p><strong>Status:</strong> Active in binary stream</p>
        </div>
        <div class="box highlight">
          <h4>AFTER CHANGE (TARGET)</h4>
          <p><strong>Field Capacity:</strong> X({comparison.after_capacity}) (12 bytes)</p>
          <p><strong>Source Schema:</strong> Expanded to PIC X(12)</p>
          <p><strong>AFP File Status:</strong> Static binary (requires JCL re-run)</p>
        </div>
      </div>
      <p class="note"><strong>Inspection Finding:</strong> {comparison.explanation}</p>
    </div>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Z-FORGE — AFP Output Visualization & Print Definition Editor ({doc.file_name})</title>
  <style>
    * {{
      box-sizing: border-box;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
      background-color: #0f172a;
      color: #f1f5f9;
      margin: 0;
      padding: 24px;
      display: flex;
      justify-content: center;
    }}
    .container {{
      max-width: 1200px;
      width: 100%;
    }}
    h1 {{
      font-size: 24px;
      margin-bottom: 4px;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .badge {{
      background: #0284c7;
      color: #ffffff;
      font-size: 12px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 4px;
      text-transform: uppercase;
    }}
    .meta {{
      font-size: 13px;
      color: #94a3b8;
      margin-bottom: 16px;
    }}
    .info-banner {{
      background: #1e293b;
      border-left: 4px solid #38bdf8;
      padding: 12px 16px;
      border-radius: 0 6px 6px 0;
      margin-bottom: 16px;
      font-size: 13px;
      line-height: 1.5;
    }}
    .arch-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 16px;
    }}
    .arch-card {{
      background: #1e293b;
      border: 1px solid #334155;
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 12px;
    }}
    .arch-card h5 {{
      margin: 0 0 4px 0;
      color: #38bdf8;
      font-size: 13px;
      text-transform: uppercase;
    }}
    .before-after-card {{
      background: #1e293b;
      border: 1px solid #334155;
      padding: 12px 16px;
      border-radius: 6px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
    }}
    .status-badge {{
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 11px;
    }}
    .badge-baseline {{
      background: #334155;
      color: #94a3b8;
    }}
    .badge-target {{
      background: #0369a1;
      color: #38bdf8;
    }}
    .editor-layout {{
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }}
    .controls-panel {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .section-title {{
      font-size: 13px;
      font-weight: 700;
      color: #38bdf8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid #334155;
      padding-bottom: 6px;
      margin-bottom: 8px;
    }}
    .form-group {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .form-group label {{
      font-size: 12px;
      color: #cbd5e1;
      font-weight: 500;
      display: flex;
      justify-content: space-between;
    }}
    .form-group input[type="range"] {{
      width: 100%;
      accent-color: #38bdf8;
    }}
    .form-group select, .form-group input[type="number"] {{
      background: #0f172a;
      border: 1px solid #334155;
      color: #f1f5f9;
      padding: 6px 10px;
      border-radius: 4px;
      font-size: 13px;
      font-family: inherit;
    }}
    .row-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}
    .checkbox-group {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: #cbd5e1;
      cursor: pointer;
    }}
    .btn-row {{
      display: flex;
      gap: 8px;
      margin-top: 6px;
    }}
    .btn {{
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: background 0.15s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }}
    .btn-primary {{
      background: #0284c7;
      color: white;
      flex: 1;
    }}
    .btn-primary:hover {{
      background: #0369a1;
    }}
    .btn-secondary {{
      background: #334155;
      color: #e2e8f0;
      flex: 1;
    }}
    .btn-secondary:hover {{
      background: #475569;
    }}
    .preview-panel {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .preview-header {{
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }}
    .preview-header h4 {{
      margin: 0;
      font-size: 14px;
      color: #cbd5e1;
    }}
    .dim-badge {{
      font-family: monospace;
      font-size: 12px;
      color: #38bdf8;
      background: #0f172a;
      border: 1px solid #334155;
      padding: 3px 8px;
      border-radius: 4px;
    }}
    .svg-wrapper {{
      max-width: 100%;
      overflow: auto;
      background: #ffffff;
      padding: 20px;
      border-radius: 6px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.4);
      display: flex;
      justify-content: center;
    }}
    .ppfa-card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 20px;
    }}
    .ppfa-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }}
    .ppfa-header h3 {{
      margin: 0;
      font-size: 15px;
      color: #f8fafc;
    }}
    pre.code-box {{
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 6px;
      padding: 14px;
      font-family: monospace;
      font-size: 12px;
      color: #38bdf8;
      overflow-x: auto;
      margin: 0;
      line-height: 1.45;
    }}
    .comparison-card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 24px;
    }}
    .comparison-card h3 {{
      margin-top: 0;
      color: #f8fafc;
      font-size: 15px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 10px;
    }}
    .box {{
      background: #0f172a;
      border: 1px solid #334155;
      padding: 12px;
      border-radius: 6px;
      font-size: 13px;
    }}
    .box h4 {{
      margin-top: 0;
      margin-bottom: 6px;
      color: #cbd5e1;
      font-size: 13px;
    }}
    .box.highlight {{
      border-color: #38bdf8;
    }}
    code {{
      background: #334155;
      padding: 2px 6px;
      border-radius: 4px;
      color: #38bdf8;
    }}
    .note {{
      font-size: 12px;
      color: #cbd5e1;
      margin-bottom: 0;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>
      Z-FORGE — AFP Output Visualization &amp; Print Definition Editor
      <span class="badge">Interactive</span>
    </h1>
    <div class="meta">
      Document: <strong>{doc.document_name}</strong> | File: <strong>{doc.file_name}</strong> |
      Structured Fields: <strong>{doc.structured_fields_count}</strong> |
      Size: <strong>{doc.raw_byte_size} bytes</strong>
    </div>

    <!-- Task 7: Architectural Distinction Banner -->
    <div class="info-banner">
      <strong>Architecture Notice:</strong> Z-FORGE is editing the semantic print definition used
      to visualize the AFP output. The original <code>CUSTRPT.AFP</code> binary remains immutable.
    </div>

    <div class="arch-grid">
      <div class="arch-card">
        <h5>AFP Data Stream</h5>
        <div>Synthetic <code>CUSTRPT.AFP</code> stream with record content and values.</div>
      </div>
      <div class="arch-card">
        <h5>PAGEDEF (Logical Page)</h5>
        <div>Controls logical page dimensions, orientation, margins, and row spacing.</div>
      </div>
      <div class="arch-card">
        <h5>FORMDEF (Form / Sheet)</h5>
        <div>Controls physical sheet presentation, duplex media, overlays, and offsets.</div>
      </div>
    </div>

    <!-- Task 4: Before / After Preview Indicator -->
    <div class="before-after-card">
      <div>
        <span class="status-badge badge-baseline">BASELINE</span>
        <strong>PAGEDEF:</strong> Statement (600 × 300 pt, Portrait) &nbsp;|&nbsp;
        <strong>FORMDEF:</strong> Simplex, Offset (0, 0)
      </div>
      <div id="afterStatus">
        <span class="status-badge badge-target">ACTIVE TARGET</span>
        <strong>PAGEDEF:</strong> {pdef.width} × {pdef.height} pt ({pdef.orientation.value})
        &nbsp;|&nbsp;
        <strong>FORMDEF:</strong> {fdef.duplex.value}
      </div>
    </div>

    <!-- Task 3: Interactive Workspace -->
    <div class="editor-layout">
      <!-- Left: Editor Controls -->
      <div class="controls-panel">
        <div class="section-title">PAGEDEF — Page Formatting</div>

        <div class="form-group">
          <label for="sizePreset">Page Size Preset</label>
          <select id="sizePreset">
            <option value="statement" selected>Statement (600 × 300 pt)</option>
            <option value="letter">US Letter (612 × 792 pt)</option>
            <option value="a4">A4 (595 × 842 pt)</option>
            <option value="custom">Custom</option>
          </select>
        </div>

        <div class="row-2">
          <div class="form-group">
            <label>Width: <span id="widthVal">{pdef.width}</span> pt</label>
            <input type="range" id="widthRange" min="300" max="900" value="{pdef.width}">
          </div>
          <div class="form-group">
            <label>Height: <span id="heightVal">{pdef.height}</span> pt</label>
            <input type="range" id="heightRange" min="200" max="900" value="{pdef.height}">
          </div>
        </div>

        <div class="form-group">
          <label for="orientationSelect">Orientation</label>
          <select id="orientationSelect">
            <option value="PORTRAIT" selected>Portrait</option>
            <option value="LANDSCAPE">Landscape</option>
          </select>
        </div>

        <div class="row-2">
          <div class="form-group">
            <label>Top Margin: <span id="marginTopVal">{pdef.margin_top}</span> pt</label>
            <input type="range" id="marginTopRange" min="10" max="80" value="{pdef.margin_top}">
          </div>
          <div class="form-group">
            <label>Bottom Margin: <span id="marginBottomVal">{pdef.margin_bottom}</span> pt</label>
            <input type="range" id="marginBottomRange" min="10" max="80"
                   value="{pdef.margin_bottom}">
          </div>
        </div>

        <div class="row-2">
          <div class="form-group">
            <label>Left Margin: <span id="marginLeftVal">{pdef.margin_left}</span> pt</label>
            <input type="range" id="marginLeftRange" min="10" max="80" value="{pdef.margin_left}">
          </div>
          <div class="form-group">
            <label>Right Margin: <span id="marginRightVal">{pdef.margin_right}</span> pt</label>
            <input type="range" id="marginRightRange" min="10" max="80" value="{pdef.margin_right}">
          </div>
        </div>

        <div class="form-group">
          <label>Line Spacing: <span id="lineSpacingVal">{pdef.line_spacing}</span> pt</label>
          <input type="range" id="lineSpacingRange" min="20" max="60" value="{pdef.line_spacing}">
        </div>

        <div class="section-title" style="margin-top: 10px;">FORMDEF — Form / Medium</div>

        <div class="form-group">
          <label for="duplexSelect">Duplexing Mode</label>
          <select id="duplexSelect">
            <option value="SIMPLEX" selected>Simplex (Single-sided)</option>
            <option value="DUPLEX">Duplex (Normal two-sided)</option>
          </select>
        </div>

        <div class="row-2">
          <div class="form-group">
            <label>Sheet Origin X: <span id="offsetXVal">{fdef.offset_x}</span> pt</label>
            <input type="range" id="offsetXRange" min="-40" max="40" value="{fdef.offset_x}">
          </div>
          <div class="form-group">
            <label>Sheet Origin Y: <span id="offsetYVal">{fdef.offset_y}</span> pt</label>
            <input type="range" id="offsetYRange" min="-40" max="40" value="{fdef.offset_y}">
          </div>
        </div>

        <div class="checkbox-group">
          <input type="checkbox" id="overlayCheck" checked>
          <label for="overlayCheck">Form Overlay Enabled (Header line)</label>
        </div>

        <div class="btn-row">
          <button type="button" class="btn btn-secondary" id="resetBtn">Reset Baseline</button>
          <button type="button" class="btn btn-secondary" id="saveJsonBtn">Save JSON</button>
          <button type="button" class="btn btn-primary" id="exportPpfaBtn">Export PPFA</button>
        </div>
      </div>

      <!-- Right: Live Print Preview -->
      <div class="preview-panel">
        <div class="preview-header">
          <h4>Live Print Layout Preview</h4>
          <span class="dim-badge" id="dimensionsBadge">{pdef.width} × {pdef.height} pt</span>
        </div>
        <div class="svg-wrapper" id="svgContainer">
          {svg_markup}
        </div>
      </div>
    </div>

    <!-- Task 5: Generated PPFA Source -->
    <div class="ppfa-card">
      <div class="ppfa-header">
        <div>
          <h3>Generated PPFA Source — semantic export</h3>
          <span style="font-size: 12px; color: #94a3b8;">
            Semantic PPFA source text export (not compiled or validated by IBM PPFA)
          </span>
        </div>
        <button type="button" class="btn btn-secondary" id="copyPpfaBtn">Copy PPFA</button>
      </div>
      <pre class="code-box" id="ppfaCode">{ppfa_markup}</pre>
    </div>

    <!-- Task 4 & Task 7: Schema Impact Comparison -->
    {comp_section}

  </div>

  <script>
    (function() {{
      const docData = {{
        title: "ZENITH BANK CUSTOMER STATEMENT",
        cidLabel: "Customer ID:",
        cidVal: "ZB000001",
        nameLabel: "Customer Name:",
        nameVal: "ALDRIDGE SIMONE J"
      }};

      const sizePreset = document.getElementById('sizePreset');
      const widthRange = document.getElementById('widthRange');
      const heightRange = document.getElementById('heightRange');
      const widthVal = document.getElementById('widthVal');
      const heightVal = document.getElementById('heightVal');
      const orientationSelect = document.getElementById('orientationSelect');

      const marginTopRange = document.getElementById('marginTopRange');
      const marginBottomRange = document.getElementById('marginBottomRange');
      const marginLeftRange = document.getElementById('marginLeftRange');
      const marginRightRange = document.getElementById('marginRightRange');
      const marginTopVal = document.getElementById('marginTopVal');
      const marginBottomVal = document.getElementById('marginBottomVal');
      const marginLeftVal = document.getElementById('marginLeftVal');
      const marginRightVal = document.getElementById('marginRightVal');

      const lineSpacingRange = document.getElementById('lineSpacingRange');
      const lineSpacingVal = document.getElementById('lineSpacingVal');

      const duplexSelect = document.getElementById('duplexSelect');
      const offsetXRange = document.getElementById('offsetXRange');
      const offsetYRange = document.getElementById('offsetYRange');
      const offsetXVal = document.getElementById('offsetXVal');
      const offsetYVal = document.getElementById('offsetYVal');
      const overlayCheck = document.getElementById('overlayCheck');

      const svgContainer = document.getElementById('svgContainer');
      const dimensionsBadge = document.getElementById('dimensionsBadge');
      const afterStatus = document.getElementById('afterStatus');
      const ppfaCode = document.getElementById('ppfaCode');

      function getEffectiveDimensions(w, h, orient) {{
        if (w === 600 && h === 300 && orient === 'PORTRAIT') {{
          return [600, 300];
        }}
        if (orient === 'LANDSCAPE') {{
          return [Math.max(w, h), Math.min(w, h)];
        }}
        return [Math.min(w, h), Math.max(w, h)];
      }}

      function updateLayout() {{
        let w = parseInt(widthRange.value, 10);
        let h = parseInt(heightRange.value, 10);
        const orient = orientationSelect.value;

        widthVal.textContent = w;
        heightVal.textContent = h;

        const [pageW, pageH] = getEffectiveDimensions(w, h, orient);

        const marginTop = parseInt(marginTopRange.value, 10);
        const marginBottom = parseInt(marginBottomRange.value, 10);
        const marginLeft = parseInt(marginLeftRange.value, 10);
        const marginRight = parseInt(marginRightRange.value, 10);
        const lineSpacing = parseInt(lineSpacingRange.value, 10);

        marginTopVal.textContent = marginTop;
        marginBottomVal.textContent = marginBottom;
        marginLeftVal.textContent = marginLeft;
        marginRightVal.textContent = marginRight;
        lineSpacingVal.textContent = lineSpacing;

        const duplex = duplexSelect.value;
        const offsetX = parseInt(offsetXRange.value, 10);
        const offsetY = parseInt(offsetYRange.value, 10);
        const overlayEnabled = overlayCheck.checked;

        offsetXVal.textContent = offsetX;
        offsetYVal.textContent = offsetY;

        const printX = offsetX + marginLeft;
        const printY = offsetY + marginTop;
        const printW = Math.max(0, pageW - marginLeft - marginRight);
        const printH = Math.max(0, pageH - marginTop - marginBottom);

        const deltaX = printX - 20;
        const deltaY = printY - 20;

        dimensionsBadge.textContent = `${{pageW}} × ${{pageH}} pt`;

        afterStatus.innerHTML = `
          <span class="status-badge badge-target">ACTIVE TARGET</span>
          <strong>PAGEDEF:</strong> ${{pageW}} × ${{pageH}} pt (${{orient}}) &nbsp;|&nbsp;
          <strong>FORMDEF:</strong> ${{duplex}} (Offset ${{offsetX}}, ${{offsetY}})
        `;

        let overlayLine = '';
        if (overlayEnabled) {{
          const lx1 = printX;
          const lx2 = printX + printW;
          const ly = printY + 75;
          overlayLine = `  <line x1="${{lx1}}" y1="${{ly}}" x2="${{lx2}}" y2="${{ly}}" ` +
            `stroke="#cbd5e1" stroke-width="1"/>\\n`;
        }}

        let duplexBadge = '';
        if (duplex === 'DUPLEX') {{
          duplexBadge = `  <rect x="${{pageW - 95}}" y="${{pageH - 26}}" width="75" height="18" ` +
            `fill="#e2e8f0" rx="3"/>\\n` +
            `  <text x="${{pageW - 85}}" y="${{pageH - 13}}" font-family="monospace" ` +
            `font-size="10" font-weight="bold" fill="#475569">DUPLEX</text>\\n`;
        }}

        const titleX = 200 + deltaX;
        const titleY = 70 + deltaY;
        const row1Y = 140 + deltaY;
        const row2Y = row1Y + lineSpacing;

        const svgHeader = `<svg width="${{pageW}}" height="${{pageH}}" ` +
          `viewBox="0 0 ${{pageW}} ${{pageH}}" xmlns="http://www.w3.org/2000/svg">\\n`;
        const svgSheet = `  <rect width="${{pageW}}" height="${{pageH}}" ` +
          `fill="#f8fafc" stroke="#cbd5e1" stroke-width="2" rx="6"/>\\n` +
          `  <rect x="${{printX}}" y="${{printY}}" width="${{printW}}" height="${{printH}}" ` +
          `fill="#ffffff" stroke="#e2e8f0" stroke-width="1" rx="4"/>\\n`;
        const svgTitle = `    <text x="${{titleX}}" y="${{titleY}}" font-family="monospace" ` +
          `font-size="16" font-weight="bold" fill="#0f172a">${{docData.title}}</text>\\n`;
        const svgRow1 = `    <text x="${{80 + deltaX}}" y="${{row1Y}}" font-family="monospace" ` +
          `font-size="13" font-weight="600" fill="#475569">${{docData.cidLabel}}</text>\\n` +
          `    <text x="${{220 + deltaX}}" y="${{row1Y}}" font-family="monospace" ` +
          `font-size="13" font-weight="bold" fill="#1e293b">${{docData.cidVal}}</text>\\n`;
        const svgRow2 = `    <text x="${{80 + deltaX}}" y="${{row2Y}}" font-family="monospace" ` +
          `font-size="13" font-weight="600" fill="#475569">${{docData.nameLabel}}</text>\\n` +
          `    <text x="${{220 + deltaX}}" y="${{row2Y}}" font-family="monospace" ` +
          `font-size="13" font-weight="bold" fill="#1e293b">${{docData.nameVal}}</text>\\n`;

        const svg = svgHeader + svgSheet + overlayLine + duplexBadge +
          svgTitle + svgRow1 + svgRow2 + '</svg>';

        svgContainer.innerHTML = svg;

        // Generate PPFA text
        const wIn = (pageW / 72.0).toFixed(2);
        const hIn = (pageH / 72.0).toFixed(2);
        const mlIn = (marginLeft / 72.0).toFixed(2);
        const mtIn = (marginTop / 72.0).toFixed(2);
        const mrIn = (marginRight / 72.0).toFixed(2);
        const mbIn = (marginBottom / 72.0).toFixed(2);
        const oxIn = (offsetX / 72.0).toFixed(2);
        const oyIn = (offsetY / 72.0).toFixed(2);
        const duplexKw = (duplex === 'DUPLEX') ? 'NORMAL' : 'NO';
        const dirKw = (orient === 'LANDSCAPE') ? 'ACROSS' : 'DOWN';

        const ppfa = `/* ============================================================ */
/* Generated PPFA Source — semantic export                      */
/* Z-FORGE IBM Z Print Engineering                              */
/* Note: Semantic export; not compiled by IBM PPFA.            */
/* ============================================================ */

FORMDEF F1CUST
    OFFSET ${{oxIn}} IN ${{oyIn}} IN
    DUPLEX ${{duplexKw}};

PAGEDEF P1CUST
    WIDTH ${{wIn}} IN
    HEIGHT ${{hIn}} IN
    DIRECTION ${{dirKw}}
    MARGINS ${{mlIn}} IN ${{mtIn}} IN ${{mrIn}} IN ${{mbIn}} IN;

    SETUNITS LINESP ${{lineSpacing}} POINTS;
    FONT FNT1 'C0S0PR10';

    PRINTLINE CHANNEL 1 POSITION MARGIN 1.0 IN FONT FNT1;
    PRINTLINE POSITION MARGIN NEXT FONT FNT1;

/* PPFA END */`;

        ppfaCode.textContent = ppfa;
      }}

      // Preset change handler
      sizePreset.addEventListener('change', function() {{
        const val = this.value;
        if (val === 'statement') {{
          widthRange.value = 600;
          heightRange.value = 300;
          orientationSelect.value = 'PORTRAIT';
        }} else if (val === 'letter') {{
          widthRange.value = 612;
          heightRange.value = 792;
          orientationSelect.value = 'PORTRAIT';
        }} else if (val === 'a4') {{
          widthRange.value = 595;
          heightRange.value = 842;
          orientationSelect.value = 'PORTRAIT';
        }}
        updateLayout();
      }});

      const inputs = [
        widthRange, heightRange, orientationSelect,
        marginTopRange, marginBottomRange, marginLeftRange, marginRightRange,
        lineSpacingRange, duplexSelect, offsetXRange, offsetYRange, overlayCheck
      ];

      inputs.forEach(input => {{
        input.addEventListener('input', () => {{
          if (input === widthRange || input === heightRange) {{
            sizePreset.value = 'custom';
          }}
          updateLayout();
        }});
        input.addEventListener('change', () => {{
          if (input === widthRange || input === heightRange) {{
            sizePreset.value = 'custom';
          }}
          updateLayout();
        }});
      }});

      // Reset to Baseline
      document.getElementById('resetBtn').addEventListener('click', () => {{
        sizePreset.value = 'statement';
        widthRange.value = 600;
        heightRange.value = 300;
        orientationSelect.value = 'PORTRAIT';
        marginTopRange.value = 20;
        marginBottomRange.value = 20;
        marginLeftRange.value = 20;
        marginRightRange.value = 20;
        lineSpacingRange.value = 35;
        duplexSelect.value = 'SIMPLEX';
        offsetXRange.value = 0;
        offsetYRange.value = 0;
        overlayCheck.checked = true;
        updateLayout();
      }});

      // Copy PPFA
      const copyBtn = document.getElementById('copyPpfaBtn');
      copyBtn.addEventListener('click', () => {{
        const text = ppfaCode.textContent;
        navigator.clipboard.writeText(text).then(() => {{
          const orig = copyBtn.textContent;
          copyBtn.textContent = 'Copied!';
          setTimeout(() => copyBtn.textContent = orig, 1800);
        }}).catch(() => {{
          alert('Failed to copy to clipboard.');
        }});
      }});

      // Download helper
      function downloadFile(content, fileName, mimeType) {{
        const blob = new Blob([content], {{ type: mimeType }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }}

      // Export PPFA
      document.getElementById('exportPpfaBtn').addEventListener('click', () => {{
        downloadFile(ppfaCode.textContent, 'CUSTRPT.ppfa', 'text/plain;charset=utf-8');
      }});

      // Save JSON
      document.getElementById('saveJsonBtn').addEventListener('click', () => {{
        const [pageW, pageH] = getEffectiveDimensions(
          parseInt(widthRange.value, 10),
          parseInt(heightRange.value, 10),
          orientationSelect.value
        );
        const cfg = {{
          page_definition: {{
            width: pageW,
            height: pageH,
            orientation: orientationSelect.value,
            margin_top: parseInt(marginTopRange.value, 10),
            margin_bottom: parseInt(marginBottomRange.value, 10),
            margin_left: parseInt(marginLeftRange.value, 10),
            margin_right: parseInt(marginRightRange.value, 10),
            line_spacing: parseInt(lineSpacingRange.value, 10)
          }},
          form_definition: {{
            duplex: duplexSelect.value,
            offset_x: parseInt(offsetXRange.value, 10),
            offset_y: parseInt(offsetYRange.value, 10),
            overlay_enabled: overlayCheck.checked
          }}
        }};
        downloadFile(JSON.stringify(cfg, null, 2), 'CUSTRPT-print-layout.json', 'application/json');
      }});

    }})();
  </script>
</body>
</html>
"""


def save_afp_visualization(
    doc: AFPDocument,
    output_target: Path | str,
    comparison: AFPComparisonResult | None = None,
    config: PrintLayoutConfig | None = None,
) -> Path:
    """Save the deterministic HTML visualization, SVG, PPFA source, and layout JSON."""
    cfg = config if config is not None else PrintLayoutConfig()
    target = Path(output_target).resolve()
    if target.suffix == ".html":
        html_file = target
        reports_dir = target.parent
    else:
        reports_dir = target
        html_file = reports_dir / "afp-custrpt.html"

    reports_dir.mkdir(parents=True, exist_ok=True)

    html_content = render_afp_html(doc, comparison, cfg)
    html_file.write_text(html_content, encoding="utf-8")

    svg_file = reports_dir / "afp-custrpt.svg"
    svg_content = render_afp_svg(doc, cfg)
    svg_file.write_text(svg_content, encoding="utf-8")

    ppfa_file = reports_dir / "CUSTRPT.ppfa"
    ppfa_content = generate_ppfa_source(cfg)
    ppfa_file.write_text(ppfa_content, encoding="utf-8")

    json_file = reports_dir / "CUSTRPT-print-layout.json"
    json_content = cfg.model_dump_json(indent=2)
    json_file.write_text(json_content, encoding="utf-8")

    return html_file
