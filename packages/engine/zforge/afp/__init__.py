"""Z-FORGE AFP subpackage — structural analysis and deterministic visualization.

Note: Provides structural parsing and visualization for the synthetic CUSTRPT.AFP.
This is NOT a full IBM AFP/PSF emulator.
"""

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

__all__ = [
    "AFPComparisonResult",
    "AFPDocument",
    "AFPElement",
    "AFPElementType",
    "AFPPage",
    "DuplexMode",
    "FormDefinition",
    "PageDefinition",
    "PageOrientation",
    "PrintLayoutConfig",
    "compare_afp_capacity",
    "generate_ppfa_source",
    "get_afp_lineage_impact",
    "parse_afp_bytes",
    "parse_afp_file",
    "render_afp_html",
    "render_afp_svg",
    "save_afp_visualization",
]
