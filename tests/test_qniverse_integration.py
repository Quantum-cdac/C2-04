"""Integration tests against the real Qniverse QSDK.

These run wherever the SDK is installed (for example the Qniverse
JupyterLab). They are skipped automatically otherwise so the offline suite
stays green. Run with: python -m pytest tests/test_qniverse_integration.py
"""

import importlib.util
import math

import pytest

if (
    importlib.util.find_spec("qniverse") is None
    and importlib.util.find_spec("Qniverse") is None
):
    pytest.skip(
        "Qniverse QSDK not installed in this environment",
        allow_module_level=True,
    )

from qasm2qniverse import convert_qasm, export_qasm, parse_qasm  # noqa: E402
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
    """qc.qasm() (documented) re-parsed must reproduce the same
    statevector. Uses export_qasm, which also handles venue SDK
    builds where qasm() prints instead of returning a string."""
    result = convert_qasm(BELL)
    exported = export_qasm(result.circuit)
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


def test_parameterized_round_trip_equivalence():
    """Built circuit's documented qasm() export must reproduce the same
    statevector, parameterized gates included - this validates the real
    builder output, not just that a circuit object exists."""
    src = """OPENQASM 2.0;
qreg q[2];
creg c[2];
rx(pi/2) q[0];
crz(pi/4) q[0], q[1];
u3(pi/3, pi/4, -pi/8) q[1];
measure q -> c;
"""
    result = convert_qasm(src)
    reimported, report = parse_qasm(export_qasm(result.circuit))
    assert not report.errors
    import numpy as np

    a, b = simulate(result.ir), simulate(reimported)
    assert abs(np.vdot(a, b)) ** 2 == pytest.approx(1.0)
