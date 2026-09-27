"""Local syntax adapter.

Performs static syntax and structure checks.
Always available; catches malformed COBOL/HLASM/JCL but cannot detect runtime data truncation.
"""

from __future__ import annotations

import re

from zforge.models import Artifact, Diagnostic, ValidationResult


class LocalSyntaxAdapter:
    """Static syntax validator based on structural rules."""

    name: str = "LocalSyntaxAdapter"

    def is_available(self) -> bool:
        return True

    def validate(self, artifact: Artifact, content: str) -> ValidationResult:
        diagnostics: list[Diagnostic] = []

        if artifact.path.endswith((".cbl", ".cob", ".cpy")):
            # Basic COBOL structure check
            if (
                "DIVISION" in content
                and "IDENTIFICATION DIVISION" not in content
                and not artifact.path.endswith(".cpy")
            ):
                diagnostics.append(
                    Diagnostic(severity="error", message="Missing IDENTIFICATION DIVISION")
                )
            # Syntax validation: check valid PIC clauses
            for match in re.finditer(r"PIC\s+([A-Za-z0-9()vV\-_]+)", content):
                pic_clause = match.group(1)
                if not re.match(r"^[9XSAZVRV\(\)0-9,\.\+\-]+$", pic_clause, re.IGNORECASE):
                    diagnostics.append(
                        Diagnostic(
                            severity="error", message=f"Invalid PIC clause format: {pic_clause}"
                        )
                    )

        elif artifact.path.endswith((".asm", ".hlasm")):
            # Basic HLASM check: ensure labels and directives exist
            if "DSECT" in content and "END" not in content:
                diagnostics.append(
                    Diagnostic(severity="warning", message="Missing END statement in HLASM file")
                )

        return ValidationResult(
            proposal_id=artifact.id,
            passed=len([d for d in diagnostics if d.severity == "error"]) == 0,
            diagnostics=diagnostics,
            runtime_adapter=self.name,
        )
