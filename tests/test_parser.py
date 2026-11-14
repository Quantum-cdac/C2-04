"""Parser correctness tests for the supported OpenQASM 2.0/3.0 subset."""

import math

import pytest

from qasm2qniverse import QasmSyntaxError, parse_qasm


BELL_2 = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
barrier q;
measure q[0] -> c[0];
measure q[1] -> c[1];
"""

GHZ_3 = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
bit[3] c;
h q[0];
cx q[0], q[1];
cx q[1], q[2];
c = measure q;
"""


def test_version_detection():
    ir, report = parse_qasm(BELL_2)
    assert ir.version == "2.0"
    assert report.detected_version == "2.0"
    ir3, report3 = parse_qasm(GHZ_3)
    assert ir3.version == "3.0"
    assert report3.detected_version == "3.0"


def test_forced_version_mismatch_warns():
    _, report = parse_qasm(BELL_2, version="3.0")
    assert report.warnings
    assert "overrides" in report.warnings[0].message


def test_bell_structure():
    ir, report = parse_qasm(BELL_2)
    assert report.status == "success"
    assert ir.num_qubits == 2 and ir.num_clbits == 2
    kinds = [op.kind for op in ir.operations]
    assert kinds == ["gate", "gate", "barrier", "measure", "measure"]
    assert ir.operations[0].name == "h"
    assert ir.operations[1].name == "cx"
    assert ir.operations[1].qargs == [("q", 0), ("q", 1)]
    assert ir.operations[3].cargs == [("c", 0)]


def test_parameter_expressions():
    src = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
rx(pi/2) q[0];
u3(pi/3, -pi/4, 2*pi) q[0];
"""
    ir, _ = parse_qasm(src)
    rx, u3 = ir.operations
    assert rx.params == [pytest.approx(math.pi / 2)]
    assert u3.params == pytest.approx([math.pi / 3, -math.pi / 4, 2 * math.pi])


def test_multiple_registers():
    src = """OPENQASM 3.0;
qubit[2] a;
qubit[1] b;
bit[1] c;
x b[0];
cx a[0], b[0];
c[0] = measure b[0];
"""
    ir, report = parse_qasm(src)
    assert [r.name for r in ir.qregs] == ["a", "b"]
    assert ir.operations[1].qargs == [("a", 0), ("b", 0)]
    assert report.status == "success"


def test_whole_register_gate_and_measure_expansion():
    src = """OPENQASM 2.0;
qreg q[2];
creg c[2];
h q;
measure q -> c;
"""
    ir, _ = parse_qasm(src)
    assert [op.name for op in ir.operations[:2]] == ["h", "h"]
    assert ir.operations[1].qargs == [("q", 1)]
    measures = [op for op in ir.operations if op.kind == "measure"]
    assert len(measures) == 2
    assert measures[1].cargs == [("c", 1)]


def test_barrier_without_arguments_covers_all_qubits():
    src = "OPENQASM 3.0;\nqubit[2] q;\nbarrier;\n"
    ir, _ = parse_qasm(src)
    assert ir.operations[0].qargs == [("q", 0), ("q", 1)]


def test_register_renaming_warns():
    src = "OPENQASM 2.0;\nqreg q_1[1];\nx q_1[0];\n"
    ir, report = parse_qasm(src)
    assert ir.qregs[0].effective_sdk_name == "q"
    assert any("renamed" in w.message for w in report.warnings)
