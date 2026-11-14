"""Integration tests against the real Qniverse QSDK.

These run wherever the SDK is installed (for example the Qniverse
JupyterLab). They are skipped automatically otherwise so the offline suite
stays green. Run with: python -m pytest tests/test_qniverse_integration.py
"""

import math

import pytest

qniverse = pytest.importorskip(
    "Qniverse", reason="Qniverse QSDK not installed in this environment"
)

from qasm2qniverse import convert_qasm, parse_qasm  # noqa: E402
from qasm2qniverse.simulator import simulate  # noqa: E402

BELL = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
"""


def test_build_returns_qniverse_circuit():
    result = convert_qasm(BELL)
    assert result.report.status == "success"
    assert result.circuit is not None
    assert result.circuit.__class__.__name__ == "QniverseCircuit"


def test_round_trip_through_documented_qasm_export():
    """qc.qasm() (documented) re-parsed must reproduce the same statevector."""
    result = convert_qasm(BELL)
    exported = result.circuit.qasm()
    reimported, report = parse_qasm(exported)
    assert not report.errors
    import numpy as np

    a, b = simulate(result.ir), simulate(reimported)
    assert abs(np.vdot(a, b)) ** 2 == pytest.approx(1.0)


def test_parameterized_program_builds():
    src = """OPENQASM 3.0;
qubit[2] q;
rx(pi/2) q[0];
crz(pi/4) q[0], q[1];
"""
    result = convert_qasm(src)
    assert result.report.status == "success"
    assert math.isclose(result.ir.operations[0].params[0], math.pi / 2)
