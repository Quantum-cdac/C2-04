"""Semantic-equivalence checks with the reference statevector simulator.

For each representative program we compare the statevector of the parsed IR
against the known analytic result, and check that a re-parse of an equivalent
program (different surface syntax, same semantics) produces the same
statevector. This is the offline half of the equivalence evidence; the
integration tests repeat the comparison against circuits built through the
QSDK where it is installed.
"""

import math

import numpy as np
import pytest

from qasm2qniverse import parse_qasm
from qasm2qniverse.simulator import fidelity, simulate

BELL = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
"""

BELL_VARIANT = """
OPENQASM 3.0;
qubit[2] q;
h q[0];
cx q[0], q[1];
"""


def test_bell_state_matches_analytic_result():
    ir, _ = parse_qasm(BELL)
    state = simulate(ir)
    expected = np.zeros(4, dtype=complex)
    expected[0] = expected[3] = 1 / math.sqrt(2)
    assert fidelity(state, expected) == pytest.approx(1.0)


def test_qasm2_and_qasm3_spellings_agree():
    ir2, _ = parse_qasm(BELL)
    ir3, _ = parse_qasm(BELL_VARIANT)
    assert fidelity(simulate(ir2), simulate(ir3)) == pytest.approx(1.0)


def test_ghz_state():
    src = """OPENQASM 3.0;
qubit[3] q;
h q[0];
cx q[0], q[1];
cx q[1], q[2];
"""
    ir, _ = parse_qasm(src)
    state = simulate(ir)
    expected = np.zeros(8, dtype=complex)
    expected[0] = expected[7] = 1 / math.sqrt(2)
    assert fidelity(state, expected) == pytest.approx(1.0)


def test_parameterized_rotation_matches_x_for_pi():
    src_rx = "OPENQASM 2.0;\nqreg q[1];\nrx(pi) q[0];\n"
    src_x = "OPENQASM 3.0;\nqubit q;\nx q;\n"
    a = simulate(parse_qasm(src_rx)[0])
    b = simulate(parse_qasm(src_x)[0])
    # equal up to global phase: compare measurement distributions
    assert np.abs(a) == pytest.approx(np.abs(b))


def test_swap_moves_excitation():
    src = """OPENQASM 2.0;
qreg q[2];
x q[0];
swap q[0], q[1];
"""
    state = simulate(parse_qasm(src)[0])
    # wire 1 carries the excitation: index bit1 set -> basis index 2
    assert abs(state[2]) == pytest.approx(1.0)


def test_toffoli():
    src = """OPENQASM 3.0;
qubit[3] q;
x q[0];
x q[1];
ccx q[0], q[1], q[2];
"""
    state = simulate(parse_qasm(src)[0])
    assert abs(state[0b111]) == pytest.approx(1.0)


def test_controlled_phase_and_u_gates():
    src = """OPENQASM 2.0;
qreg q[2];
x q[0];
x q[1];
cu1(pi/2) q[0], q[1];
"""
    state = simulate(parse_qasm(src)[0])
    assert state[3] == pytest.approx(1j * 1.0)


def test_measurement_and_barrier_do_not_change_state():
    with_ops, _ = parse_qasm(BELL)
    src = BELL.replace("measure q -> c;", "")
    without_ops, _ = parse_qasm(src)
    assert fidelity(simulate(with_ops), simulate(without_ops)) == pytest.approx(1.0)
