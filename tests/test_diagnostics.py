"""Error-handling and unsupported-construct diagnostics."""

import pytest

from qasm2qniverse import QasmSyntaxError, parse_qasm


def test_missing_header_is_fatal():
    with pytest.raises(QasmSyntaxError) as info:
        parse_qasm("qreg q[1];")
    assert info.value.report.errors


def test_unknown_gate_reported_with_line():
    src = "OPENQASM 2.0;\nqreg q[1];\nsx q[0];\n"
    _, report = parse_qasm(src)
    assert report.status == "partial"
    entry = report.unsupported_statements[0]
    assert "sx" in entry.message
    assert entry.line == 3


def test_custom_gate_definition_unsupported_but_parsing_continues():
    src = """OPENQASM 3.0;
qubit[1] q;
gate mygate a { x a; }
mygate q[0];
h q[0];
"""
    ir, report = parse_qasm(src)
    assert report.status == "partial"
    kinds = [e.kind for e in report.entries]
    assert kinds.count("unsupported") == 2  # definition + use
    assert ir.operations[-1].name == "h"  # later statements still parsed


def test_dynamic_constructs_unsupported():
    src = """OPENQASM 3.0;
qubit[1] q;
bit c;
c = measure q[0];
if (c == 1) x q[0];
"""
    _, report = parse_qasm(src)
    assert any("dynamic" in e.message for e in report.unsupported_statements)


def test_invalid_index_raises_with_report():
    with pytest.raises(QasmSyntaxError) as info:
        parse_qasm("OPENQASM 2.0;\nqreg q[1];\nx q[5];\n")
    assert "out of range" in str(info.value)
    assert info.value.report.errors


def test_undeclared_register_raises():
    with pytest.raises(QasmSyntaxError):
        parse_qasm("OPENQASM 2.0;\nqreg q[1];\nx r[0];\n")


def test_wrong_parameter_count_raises():
    with pytest.raises(QasmSyntaxError):
        parse_qasm("OPENQASM 2.0;\nqreg q[1];\nrx(pi/2, pi) q[0];\n")


def test_unsupported_parameter_expression_raises():
    with pytest.raises(QasmSyntaxError):
        parse_qasm("OPENQASM 2.0;\nqreg q[1];\nrx(theta) q[0];\n")
