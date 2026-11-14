"""Offline checks for the gate-decomposition fallback (qasm2qniverse.lowering).

Two properties are proven here:

1. Every decomposition rule preserves the gate's unitary up to global phase
   (validation approach cross-checked against a teammate's independent
   implementation): the native gate matrix from the reference simulator is
   compared with the unitary of the fully expanded decomposition, including
   permuted operand orders.

2. The builder actually engages the fallback: against a fake SDK whose gate
   catalog lacks ccx/cp/crz, conversion still succeeds, records one warning
   per substituted gate, and the recorded circuit is phase-equivalent to the
   native-gate simulation.
"""

import pytest

import qasm2qniverse.builder as builder_mod
from qasm2qniverse import convert_qasm, lowering
from qasm2qniverse.ir import CircuitIR, Operation, Register
from qasm2qniverse.simulator import phase_equivalent, simulate, unitary

# Decompose until only these remain (the minimal set every QSDK build that
# follows the documented gate catalog provides, and all venue-verified).
BASE = {"h", "x", "s", "sdg", "t", "tdg", "rx", "ry", "rz", "p", "cx"}

_FORCE = lambda name: name in BASE  # noqa: E731


def _one_op_ir(name, params, wires, n):
    op = Operation(
        "gate", name=name, params=list(params),
        qargs=[("q", i) for i in wires],
    )
    return CircuitIR("3.0", [Register("q", n)], [], [op])


def _expanded_ir(name, params, wires, n):
    steps = lowering.lower_steps(
        name, list(params), [("q", i) for i in wires], _FORCE)
    assert steps is not None, name
    assert all(s[0] in BASE for s in steps), (name, steps)
    ops = [
        Operation("gate", name=s[0], params=s[1], qargs=s[2]) for s in steps
    ]
    return CircuitIR("3.0", [Register("q", n)], [], ops)


CASES = [
    ("u1", [0.7], [0], 2),
    ("u2", [0.3, 1.1], [1], 2),
    ("u3", [0.4, 1.2, -0.9], [0], 2),
    ("cy", [], [1, 0], 2),
    ("cz", [], [1, 0], 2),
    ("ch", [], [0, 1], 2),
    ("swap", [], [0, 1], 2),
    ("ccx", [], [2, 0, 1], 3),
    ("cswap", [], [1, 2, 0], 3),
    ("crz", [0.8], [1, 0], 2),
    ("cp", [1.3], [0, 1], 2),
    ("cu1", [0.6], [0, 1], 2),
    ("cs", [], [0, 1], 2),
    ("ct", [], [1, 0], 2),
    ("csdg", [], [0, 1], 2),
    ("ctdg", [], [0, 1], 2),
    ("crx", [0.9], [0, 1], 2),
    ("cry", [-0.4], [1, 0], 2),
    ("cu2", [0.5, 0.2], [0, 1], 2),
    ("cu3", [0.4, 1.2, -0.9], [1, 0], 2),
]


@pytest.mark.parametrize("name,params,wires,n", CASES)
def test_rule_matches_native_unitary_up_to_phase(name, params, wires, n):
    native = unitary(_one_op_ir(name, params, wires, n))
    lowered = unitary(_expanded_ir(name, params, wires, n))
    assert phase_equivalent(native, lowered), name


def test_unruleable_gate_returns_none():
    assert lowering.lower_steps("c3x", [], [("q", i) for i in range(4)],
                                _FORCE) is None
    assert lowering.lower_steps("c5x", [], [("q", i) for i in range(6)],
                                _FORCE) is None


# --- builder fallback against a fake SDK missing ccx / cp / crz -----------


class _FakeReg:
    def __init__(self, size, name):
        self.size, self.name = size, name

    def __getitem__(self, i):
        return (self.name, i)


class _FakeGate:
    def __init__(self, name, params=()):
        self.name, self.params = name, tuple(params)


class _FakeGates:
    """Gate catalog of an SDK build that lacks ccx, cp and crz."""

    measure = _FakeGate("measure")
    barrier = _FakeGate("barrier")
    reset = _FakeGate("reset")

    def __getattr__(self, name):
        if name in ("h", "x", "s", "sdg", "t", "tdg", "cx"):
            return _FakeGate(name)
        if name in ("rx", "ry", "rz", "p"):
            return lambda *ps, _n=name: _FakeGate(_n, ps)
        raise AttributeError(name)


class _FakeCircuit:
    def __init__(self):
        self.registers = []
        self.added = []

    def add_register(self, reg):
        self.registers.append(reg)

    def add_gate(self, gate, *wires):
        self.added.append((gate.name, gate.params, wires))


def _fake_sdk():
    return _FakeCircuit, _FakeReg, _FakeReg, _FakeGates()


def test_builder_decomposes_gates_missing_from_sdk(monkeypatch):
    monkeypatch.setattr(builder_mod, "_require_sdk", _fake_sdk)
    src = """OPENQASM 2.0;
qreg q[3];
h q[0];
ccx q[0], q[1], q[2];
cp(0.7) q[0], q[2];
crz(pi/5) q[1], q[2];
"""
    result = convert_qasm(src)
    assert result.report.status == "success"
    warned = [w.message for w in result.report.warnings]
    assert any("'ccx'" in m for m in warned)
    assert any("'cp'" in m for m in warned)
    assert any("'crz'" in m for m in warned)
    used = [g for g, _, _ in result.circuit.added]
    assert "ccx" not in used and "cp" not in used and "crz" not in used
    # ccx contributes its 15-primitive sequence
    assert len(used) == 1 + 15 + 5 + 4

    lowered_ir = CircuitIR(
        result.ir.version, result.ir.qregs, result.ir.cregs,
        [
            Operation("gate", name=g, params=list(ps), qargs=list(ws))
            for g, ps, ws in result.circuit.added
        ],
    )
    assert phase_equivalent(simulate(result.ir), simulate(lowered_ir))
