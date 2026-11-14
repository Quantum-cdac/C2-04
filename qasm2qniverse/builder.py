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

import contextlib
import importlib
import io
import types

from . import lowering
from .errors import QasmConversionError
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
    """Import the Qniverse QSDK.

    The documented package name is ``Qniverse``; the Qniverse Jupyter
    Notebook ships the same SDK preinstalled as lowercase ``qniverse``
    (verified 2026-11-14: class ``qniverse.QniverseCircuit.QniverseCircuit``,
    Python 3.11 conda image). Both are accepted; documented names are
    looked up in the package top level and its ``QniverseCircuit``
    submodule, matching the layouts of both distributions.
    """
    pkg = None
    for name in ("qniverse", "Qniverse"):  # noqa: N813
        try:
            pkg = importlib.import_module(name)
            break
        except ImportError:
            continue
    if pkg is None:
        raise ImportError(
            "The Qniverse QSDK is required to build QniverseCircuit objects. "
            "Install it with 'pip install qniverse' (see "
            "https://qniverse.in/docs-category/qsdk/introduction/getting_started.html) "
            "or run inside the Qniverse JupyterLab, where the SDK is provided."
        )
    try:
        circuit_mod = importlib.import_module(pkg.__name__ + ".QniverseCircuit")
    except ImportError:
        circuit_mod = None

    def _find(attr):
        # Prefer a non-module attribute: importing the QniverseCircuit
        # submodule can leave a module object under the same name.
        module_hit = None
        for mod in (pkg, circuit_mod):
            if mod is not None and hasattr(mod, attr):
                obj = getattr(mod, attr)
                if not isinstance(obj, types.ModuleType):
                    return obj
                module_hit = module_hit or obj
        if module_hit is not None:
            return module_hit
        raise ImportError(
            "the %r SDK distribution does not expose %s where the QSDK "
            "documentation places it" % (pkg.__name__, attr)
        )

    try:
        gates_mod = importlib.import_module(pkg.__name__ + ".gates")
    except ImportError:
        gates_mod = None

    class _Gates:
        """Gate lookup: documented ``gates`` submodule first, then the
        package top level (the lowercase venue distribution re-exports the
        gates there)."""

        def __getattr__(self, attr):
            for mod in (gates_mod, pkg):
                if mod is not None and hasattr(mod, attr):
                    return getattr(mod, attr)
            raise AttributeError(attr)

    qgates = _Gates()
    return (
        _find("QniverseCircuit"),
        _find("QuantumRegister"),
        _find("ClassicalRegister"),
        qgates,
    )


def export_qasm(circuit):
    """Return the circuit's QASM 2.0 text via the documented ``qasm()``.

    The documented signature is ``qasm(self, shots=None)``. The venue SDK
    build (lowercase ``qniverse``, verified 2026-11-14) prints the program
    and returns ``None``, so capture stdout when the return value is not a
    string. Raises RuntimeError if neither yields QASM text.
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = circuit.qasm()
    if isinstance(out, str) and out.strip():
        return out
    text = buf.getvalue()
    if text.strip():
        return text
    raise RuntimeError("QniverseCircuit.qasm() produced no QASM output")


def _sdk_has(qgates, name):
    """True when the installed SDK exposes this gate object."""
    return hasattr(qgates, name)


def build_circuit(ir, report=None):
    """Build a QniverseCircuit from a parsed CircuitIR.

    Returns the ``QniverseCircuit`` object. Assumes the IR passed validation
    (registers declared, indices in range); the parser guarantees this.

    Gates are taken from the installed SDK whenever it exposes them. When a
    gate is absent from the installed build, a decomposition from
    ``lowering`` is substituted and recorded as a warning in ``report``
    (when given) - the conversion never silently rewrites a gate. Gates
    with no applicable rule raise QasmConversionError.
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
            if _sdk_has(qgates, op.name):
                steps = [(op.name, list(op.params), list(op.qargs))]
            else:
                steps = lowering.lower_steps(
                    op.name, op.params, op.qargs,
                    lambda n: _sdk_has(qgates, n),
                )
                if steps is None:
                    raise QasmConversionError(
                        "gate %r is not exposed by the installed QSDK build "
                        "and no decomposition rule reaches it" % op.name,
                    )
                if report is not None:
                    report.warn(
                        "gate %r is not exposed by the installed QSDK build; "
                        "substituted an equivalent decomposition (%s) - exact "
                        "up to global phase, measurement outcomes unchanged"
                        % (op.name, ", ".join(sorted({s[0] for s in steps}))),
                        line=op.line,
                    )
            for step_name, step_params, step_wires in steps:
                if step_name in _ZERO_PARAM:
                    gate = getattr(qgates, step_name)
                elif step_name in _PARAM_GATES:
                    gate = getattr(qgates, step_name)(*step_params)
                else:  # pragma: no cover - lowering only emits mapped names
                    raise ValueError("no documented QSDK gate for %r" % step_name)
                circuit.add_gate(gate, *[qubit(w) for w in step_wires])
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
