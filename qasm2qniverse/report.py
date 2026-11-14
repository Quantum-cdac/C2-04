"""Structured conversion report returned alongside the circuit."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReportEntry:
    """One diagnostic: warning, unsupported statement or error."""

    kind: str  # "warning" | "unsupported" | "error"
    message: str
    line: Optional[int] = None
    statement: Optional[str] = None

    def to_dict(self):
        out = {"kind": self.kind, "message": self.message}
        if self.line is not None:
            out["line"] = self.line
        if self.statement:
            out["statement"] = self.statement
        return out


@dataclass
class ConversionReport:
    """What happened during a conversion.

    status: "success" (everything mapped), "partial" (some statements
        unsupported or skipped), or "failed" (no usable circuit produced).
    """

    detected_version: Optional[str] = None
    status: str = "success"
    mapped_operations: int = 0
    quantum_registers: List[dict] = field(default_factory=list)
    classical_registers: List[dict] = field(default_factory=list)
    entries: List[ReportEntry] = field(default_factory=list)

    def _add(self, kind, message, line=None, statement=None):
        self.entries.append(ReportEntry(kind, message, line, statement))

    def warn(self, message, line=None, statement=None):
        self._add("warning", message, line, statement)

    def unsupported(self, message, line=None, statement=None):
        self._add("unsupported", message, line, statement)
        if self.status == "success":
            self.status = "partial"

    def error(self, message, line=None, statement=None):
        self._add("error", message, line, statement)
        self.status = "failed"

    @property
    def warnings(self):
        return [e for e in self.entries if e.kind == "warning"]

    @property
    def unsupported_statements(self):
        return [e for e in self.entries if e.kind == "unsupported"]

    @property
    def errors(self):
        return [e for e in self.entries if e.kind == "error"]

    def to_dict(self):
        return {
            "status": self.status,
            "detected_version": self.detected_version,
            "mapped_operations": self.mapped_operations,
            "quantum_registers": self.quantum_registers,
            "classical_registers": self.classical_registers,
            "warnings": [e.to_dict() for e in self.warnings],
            "unsupported_statements": [e.to_dict() for e in self.unsupported_statements],
            "errors": [e.to_dict() for e in self.errors],
        }
