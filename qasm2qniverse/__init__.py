"""OpenQASM 2.0/3.0 to QniverseCircuit converter (QC-C2-04).

Public API:
    parse_qasm(source, version=None) -> (CircuitIR, ConversionReport)
    build_circuit(ir) -> QniverseCircuit (requires the Qniverse QSDK)
    export_qasm(circuit) -> str (documented qasm() export; captures
        stdout on SDK builds where qasm() prints instead of returning)
    convert_qasm(source, version=None) -> ConversionResult
"""

from dataclasses import dataclass

from .builder import build_circuit, export_qasm
from .errors import QasmConversionError, QasmSyntaxError
from .ir import CircuitIR, Operation, Register
from .parser import parse_qasm
from .report import ConversionReport, ReportEntry

__version__ = "0.1.0"

__all__ = [
    "ConversionResult",
    "ConversionReport",
    "ReportEntry",
    "CircuitIR",
    "Operation",
    "Register",
    "QasmConversionError",
    "QasmSyntaxError",
    "parse_qasm",
    "build_circuit",
    "convert_qasm",
]


@dataclass
class ConversionResult:
    """Result of convert_qasm: the circuit plus everything that happened."""

    circuit: object  # QniverseCircuit
    ir: CircuitIR
    report: ConversionReport


def convert_qasm(source, version=None, allow_partial=False):
    """Convert an OpenQASM 2.0/3.0 source string into a QniverseCircuit.

    Returns a ConversionResult with the circuit, the intermediate
    representation and a report (detected version, mapped operations,
    warnings and unsupported statements).

    Strict by default: when any statement is unsupported the conversion
    raises QasmConversionError with the report attached, instead of handing
    back a circuit that silently omits part of the source program. Pass
    ``allow_partial=True`` for a diagnostics-only partial build: the returned
    circuit then contains the accepted statements only and the report is
    marked accordingly. Fatal syntax errors always raise QasmSyntaxError with
    the partial report attached as ``exc.report``.
    """
    ir, report = parse_qasm(source, version=version)
    if report.status != "success":
        if not allow_partial:
            exc = QasmConversionError(
                "source contains %d unsupported statement(s); no circuit built. "
                "Pass allow_partial=True for a diagnostics-only partial build."
                % len(report.unsupported_statements)
            )
            exc.report = report
            raise exc
        report.warn(
            "partial build: circuit contains only the %d accepted operation(s); "
            "%d unsupported statement(s) are excluded - diagnostics mode, not "
            "an equivalent of the full source"
            % (report.mapped_operations, len(report.unsupported_statements))
        )
    circuit = build_circuit(ir, report=report)
    return ConversionResult(circuit=circuit, ir=ir, report=report)
