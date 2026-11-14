"""Small reference statevector simulator over the converter IR.

Used by the validation tests to demonstrate semantic equivalence: the IR of a
source QASM program and the IR recovered from the generated circuit must
produce the same statevector. Independent of the Qniverse SDK, so correctness
tests run anywhere (the QSDK adapter is covered by the integration tests).

Convention: qubit wires follow global declaration order; wire 0 is the least
significant bit of the computational-basis index.
"""

import math

import numpy as np

from .ir import CircuitIR


def _gate_matrix(name, params):
    c = np.cos
    s = np.sin
    e = np.exp
    i = 1j
    if name == "id":
        return np.eye(2, dtype=complex)
    if name == "x":
        return np.array([[0, 1], [1, 0]], dtype=complex)
    if name == "y":
        return np.array([[0, -i], [i, 0]], dtype=complex)
    if name == "z":
        return np.array([[1, 0], [0, -1]], dtype=complex)
    if name == "h":
        return np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)
    if name == "s":
        return np.array([[1, 0], [0, i]], dtype=complex)
    if name == "sdg":
        return np.array([[1, 0], [0, -i]], dtype=complex)
    if name == "t":
        return np.array([[1, 0], [0, e(i * math.pi / 4)]], dtype=complex)
    if name == "tdg":
        return np.array([[1, 0], [0, e(-i * math.pi / 4)]], dtype=complex)
    if name == "rx":
        (t,) = params
        return np.array(
            [[c(t / 2), -i * s(t / 2)], [-i * s(t / 2), c(t / 2)]], dtype=complex
        )
    if name == "ry":
        (t,) = params
        return np.array(
            [[c(t / 2), -s(t / 2)], [s(t / 2), c(t / 2)]], dtype=complex
        )
    if name == "rz":
        (p,) = params
        return np.array([[e(-i * p / 2), 0], [0, e(i * p / 2)]], dtype=complex)
    if name in ("u1", "p"):
        (lam,) = params
        return np.array([[1, 0], [0, e(i * lam)]], dtype=complex)
    if name == "u2":
        phi, lam = params
        return _gate_matrix("u3", [math.pi / 2, phi, lam])
    if name == "u3":
        t, phi, lam = params
        return np.array(
            [
                [c(t / 2), -e(i * lam) * s(t / 2)],
                [e(i * phi) * s(t / 2), e(i * (phi + lam)) * c(t / 2)],
            ],
            dtype=complex,
        )
    raise ValueError("no reference matrix for gate %r" % name)


def _controlled(matrix, num_controls):
    dim = matrix.shape[0]
    total = (2 ** num_controls) * dim
    out = np.eye(total, dtype=complex)
    out[total - dim:, total - dim:] = matrix
    return out


_CONTROLLED_PREFIX = {
    "c": 1,   # cx, cy, cz, ch, cs, ct, csdg, ctdg, crx, cry, crz, cu1, cp, cu2, cu3
    "cc": 2,  # ccx
    "c3": 3,  # c3x
    "c4": 4,  # c4x
    "c5": 5,  # c5x
}


def _operation_matrix(op):
    name = op.name
    if name == "swap":
        return np.array(
            [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex
        )
    if name == "cswap":
        return _controlled(_operation_matrix(type(op)("gate", name="swap")), 1)
    for prefix, controls in sorted(_CONTROLLED_PREFIX.items(), key=lambda kv: -len(kv[0])):
        if name.startswith(prefix) and name != "cswap":
            base_name = name[len(prefix):]
            if base_name in ("x", "y", "z", "h", "s", "t", "sdg", "tdg",
                             "rx", "ry", "rz", "u1", "u2", "u3", "p"):
                return _controlled(_gate_matrix(base_name, op.params), controls)
    return _gate_matrix(name, op.params)


def simulate(ir, num_qubits=None):
    """Return the statevector (numpy array) produced by the IR's gate operations.

    Measurement and barrier operations do not change the statevector; resets
    are treated as unsupported here and raise ValueError.
    """
    wires = ir.qubit_wires()
    n = num_qubits if num_qubits is not None else len(wires)
    index_of = {wire: i for i, wire in enumerate(wires)}
    # Internally axis i of the tensor is wire i; flattened only at the end so
    # that wire 0 is the least significant bit of the basis index.
    tensor = np.zeros([2] * n, dtype=complex)
    tensor[(0,) * n] = 1.0
    for op in ir.operations:
        if op.kind in ("measure", "barrier"):
            continue
        if op.kind == "reset":
            raise ValueError("reset is not supported by the reference simulator")
        targets = [index_of[w] for w in op.qargs]
        if len(set(targets)) != len(targets):
            raise ValueError("duplicate qubit in operation")
        matrix = _operation_matrix(op)
        tensor = _apply(tensor, matrix, targets, n)
    if n == 0:
        return tensor.reshape(-1)
    return np.transpose(tensor, list(reversed(range(n)))).reshape(-1)


def _apply(tensor, matrix, targets, n):
    """Apply a k-qubit matrix to the given target wires (order = matrix order).

    ``tensor`` uses axis i for wire i; the matrix acts on the targets with the
    first target as the most significant qubit of the k-qubit block.
    """
    k = len(targets)
    other = [i for i in range(n) if i not in targets]
    perm = targets + other
    moved = np.transpose(tensor, perm).reshape(2 ** k, -1)
    moved = matrix @ moved
    moved = moved.reshape([2] * n)
    inverse = [perm.index(i) for i in range(n)]
    return np.transpose(moved, inverse)


def fidelity(a, b):
    """|psi|^2 overlap between two statevectors."""
    return float(abs(np.vdot(a, b)) ** 2)
