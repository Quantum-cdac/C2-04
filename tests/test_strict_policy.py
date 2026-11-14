"""Strict-conversion policy: partial input must not yield an executable
circuit unless the caller explicitly opts into a diagnostics-only build."""

import pytest

import qasm2qniverse
from qasm2qniverse import QasmConversionError, convert_qasm

PARTIAL = """OPENQASM 3.0;
qubit[1] q;
bit c;
c = measure q[0];
if (c == 1) x q[0];
"""


def test_partial_source_raises_by_default_with_report():
    with pytest.raises(QasmConversionError) as info:
        convert_qasm(PARTIAL)
    report = info.value.report
    assert report.status == "partial"
    assert report.unsupported_statements
    assert "allow_partial" in str(info.value)


def test_allow_partial_is_explicitly_marked(monkeypatch):
    monkeypatch.setattr(qasm2qniverse, "build_circuit", lambda ir: "circuit-stub")
    result = convert_qasm(PARTIAL, allow_partial=True)
    assert result.circuit == "circuit-stub"
    assert any("partial build" in w.message for w in result.report.warnings)
    assert result.report.status == "partial"


def test_clean_source_still_builds(monkeypatch):
    monkeypatch.setattr(qasm2qniverse, "build_circuit", lambda ir: "circuit-stub")
    result = convert_qasm(
        "OPENQASM 2.0;\nqreg q[1];\ncreg c[1];\nh q[0];\nmeasure q[0] -> c[0];\n"
    )
    assert result.report.status == "success"
    assert result.circuit == "circuit-stub"
