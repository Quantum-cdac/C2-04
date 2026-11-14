"""Translate the converter IR into a QniverseCircuit.

This is the only module that imports the Qniverse SDK, and it uses documented
interfaces only (QSDK documentation, "Creating a Circuit" and "Quantum Gates"):

* ``QniverseCircuit()``, ``QuantumRegister(size, 'name')``,
  ``ClassicalRegister(size, 'name')`` and ``circuit.add_register(reg)``
* ``circuit.add_gate(gate, *wires)`` with gate objects from ``Qniverse.gates``
* parameterized gates are constructed first, e.g. ``rx(theta)``
* measurement uses ``add_gate(measure, qubit, clbit)``; ``barrier`` and
  ``reset`` take qubit wires
"""

from .ir import CircuitIR

_ZERO_PARAM = {
    "id", "x", "y", "z", "h", "s", "sdg", "t", "tdg",
    "cx", "cy", "cz", "ch", "swap", "cs", "ct", "csdg", "ctdg",
    "ccx", "cswap", "c3x", "c4x", "c5x",
}
_PARAM_GATES = {
    "rx", "ry", "rz", "u1", "p", "u2", "u3",
    "crx", "cry", "crz", "cu1", "cp", "cu2", "cu3",
}


def _require_sdk():
    try:
        from Qniverse.QniverseCircuit import (  # noqa: N813
            ClassicalRegister,
            QniverseCircuit,
            QuantumRegister,
        )
        import Qniverse.gates as qgates  # noqa: N813
    except ImportError as exc:
        raise ImportError(
            "The Qniverse QSDK is required to build QniverseCircuit objects. "
            "Install it with 'pip install qniverse' (see "
            "https://qniverse.in/docs-category/qsdk/introduction/getting_started.html) "
            "or run inside the Qniverse JupyterLab, where the SDK is provided."
        ) from exc
    return QniverseCircuit, QuantumRegister, ClassicalRegister, qgates


def build_circuit(ir):
    """Build a QniverseCircuit from a parsed CircuitIR.

    Returns the ``QniverseCircuit`` object. Assumes the IR passed validation
    (registers declared, indices in range); the parser guarantees this.
    """
    QniverseCircuit, QuantumRegister, ClassicalRegister, qgates = _require_sdk()

    circuit = QniverseCircuit()
    qreg_objs = {}
    creg_objs = {}
    for reg in ir.qregs:
        obj = QuantumRegister(reg.size, reg.effective_sdk_name)
        circuit.add_register(obj)
        qreg_objs[reg.name] = obj
    for reg in ir.cregs:
        obj = ClassicalRegister(reg.size, reg.effective_sdk_name)
        circuit.add_register(obj)
        creg_objs[reg.name] = obj

    def qubit(wire):
        return qreg_objs[wire[0]][wire[1]]

    def clbit(wire):
        return creg_objs[wire[0]][wire[1]]

    for op in ir.operations:
        if op.kind == "gate":
            if op.name in _ZERO_PARAM:
                gate = getattr(qgates, op.name)
            elif op.name in _PARAM_GATES:
                gate = getattr(qgates, op.name)(*op.params)
            else:  # pragma: no cover - parser only emits mapped names
                raise ValueError("no documented QSDK gate for %r" % op.name)
            circuit.add_gate(gate, *[qubit(w) for w in op.qargs])
        elif op.kind == "measure":
            circuit.add_gate(qgates.measure, qubit(op.qargs[0]), clbit(op.cargs[0]))
        elif op.kind == "barrier":
            circuit.add_gate(qgates.barrier, *[qubit(w) for w in op.qargs])
        elif op.kind == "reset":
            for wire in op.qargs:
                circuit.add_gate(qgates.reset, qubit(wire))
        else:  # pragma: no cover
            raise ValueError("unknown operation kind %r" % op.kind)
    return circuit
