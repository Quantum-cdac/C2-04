"""Gate decomposition rules used when the installed QSDK build lacks a gate.

The builder tries the native QSDK gate first, always. Only when the gate
object is absent from the installed SDK does it fall back to one of these
decompositions, and every substitution is recorded as a warning in the
conversion report - nothing is silently rewritten.

Correctness: each rule preserves the operation's unitary exactly, except the
ones marked "up to global phase" below, which can differ by an overall phase
factor only (unobservable in any measurement distribution). The offline
suite (tests/test_lowering.py) proves every rule against the reference
simulator's matrices, including permuted operand orders. The decomposition
set follows standard references (Nielsen & Chuang; the Qiskit/openqasm
gate equivalences) and was cross-validated against a teammate's independent
implementation of the same rules.

No rules exist for c3x/c4x/c5x (they need ancilla qubits); when the SDK
lacks one of those the builder raises a clear error instead of guessing.
"""

import math

_PI = math.pi


def _u1(params, q):
    return [("p", list(params), [q[0]])]


def _p(params, q):
    # up to global phase: p(l) = e^{i l/2} * rz(l)
    return [("rz", list(params), [q[0]])]


def _t(params, q):
    return [("p", [_PI / 4], [q[0]])]


def _tdg(params, q):
    return [("p", [-_PI / 4], [q[0]])]


def _s(params, q):
    return [("p", [_PI / 2], [q[0]])]


def _sdg(params, q):
    return [("p", [-_PI / 2], [q[0]])]


def _u2(params, q):
    phi, lam = params
    return [("u3", [_PI / 2, phi, lam], [q[0]])]


def _u3(params, q):
    # up to global phase: u3(t, f, l) = e^{i(f+l)/2} rz(l) ry(t) rz(f)
    t, phi, lam = params
    return [("rz", [lam], [q[0]]), ("ry", [t], [q[0]]), ("rz", [phi], [q[0]])]


def _cy(params, q):
    a, b = q
    return [("sdg", [], [b]), ("cx", [], [a, b]), ("s", [], [b])]


def _cz(params, q):
    a, b = q
    return [("h", [], [b]), ("cx", [], [a, b]), ("h", [], [b])]


def _ch(params, q):
    a, b = q
    return [
        ("h", [], [b]), ("sdg", [], [b]), ("cx", [], [a, b]), ("h", [], [b]),
        ("t", [], [b]), ("cx", [], [a, b]), ("t", [], [b]), ("h", [], [b]),
        ("s", [], [b]), ("x", [], [b]), ("s", [], [a]),
    ]


def _swap(params, q):
    a, b = q
    return [("cx", [], [a, b]), ("cx", [], [b, a]), ("cx", [], [a, b])]


def _ccx(params, q):
    a, b, c = q
    return [
        ("h", [], [c]), ("cx", [], [b, c]), ("tdg", [], [c]),
        ("cx", [], [a, c]), ("t", [], [c]), ("cx", [], [b, c]),
        ("tdg", [], [c]), ("cx", [], [a, c]), ("t", [], [b]),
        ("t", [], [c]), ("h", [], [c]), ("cx", [], [a, b]),
        ("t", [], [a]), ("tdg", [], [b]), ("cx", [], [a, b]),
    ]


def _cswap(params, q):
    a, b, c = q
    return [("cx", [], [c, b]), ("ccx", [], [a, b, c]), ("cx", [], [c, b])]


def _crz(params, q):
    (lam,) = params
    a, b = q
    return [
        ("rz", [lam / 2], [b]), ("cx", [], [a, b]),
        ("rz", [-lam / 2], [b]), ("cx", [], [a, b]),
    ]


def _cp(params, q):
    (lam,) = params
    a, b = q
    return [
        ("p", [lam / 2], [a]), ("cx", [], [a, b]), ("p", [-lam / 2], [b]),
        ("cx", [], [a, b]), ("p", [lam / 2], [b]),
    ]


def _cs(params, q):
    return [("cp", [_PI / 2], list(q))]


def _ct(params, q):
    return [("cp", [_PI / 4], list(q))]


def _csdg(params, q):
    return [("cp", [-_PI / 2], list(q))]


def _ctdg(params, q):
    return [("cp", [-_PI / 4], list(q))]


def _crx(params, q):
    # rx(l) = H rz(l) H exactly, so crx = h b; crz(l); h b
    (lam,) = params
    a, b = q
    return [("h", [], [b]), ("crz", [lam], [a, b]), ("h", [], [b])]


def _cry(params, q):
    # ry(l) = S rx(l) Sdg exactly, so cry = sdg b; crx(l); s b
    (lam,) = params
    a, b = q
    return [("sdg", [], [b]), ("crx", [lam], [a, b]), ("s", [], [b])]


def _cu3(params, q):
    # standard controlled-u3 decomposition (Qiskit CU3Gate definition)
    t, phi, lam = params
    a, b = q
    return [
        ("p", [(lam + phi) / 2], [a]), ("p", [(lam - phi) / 2], [b]),
        ("cx", [], [a, b]), ("u3", [-t / 2, 0, -(phi + lam) / 2], [b]),
        ("cx", [], [a, b]), ("u3", [t / 2, phi, 0], [b]),
    ]


def _cu2(params, q):
    phi, lam = params
    return [("cu3", [_PI / 2, phi, lam], list(q))]


# Gate name -> rule(params, qargs) -> list of (name, params, qargs).
# cu1 shares the controlled-phase rule with cp (same unitary).
RULES = {
    "u1": _u1, "p": _p, "t": _t, "tdg": _tdg, "s": _s, "sdg": _sdg,
    "u2": _u2, "u3": _u3,
    "cy": _cy, "cz": _cz, "ch": _ch, "swap": _swap,
    "ccx": _ccx, "cswap": _cswap,
    "crz": _crz, "cp": _cp, "cu1": _cp,
    "cs": _cs, "ct": _ct, "csdg": _csdg, "ctdg": _ctdg,
    "crx": _crx, "cry": _cry, "cu2": _cu2, "cu3": _cu3,
}

MAX_DEPTH = 8


def lower_steps(name, params, qargs, has, _depth=0):
    """Expand one gate operation into steps the installed SDK provides.

    ``has(gate_name)`` reports whether the SDK exposes that gate. Returns a
    flat list of ``(name, params, qargs)`` steps - the operation itself
    unchanged when the SDK has it natively - or ``None`` when the gate is
    missing and no rule chain reaches available gates.
    """
    if has(name):
        return [(name, list(params), list(qargs))]
    rule = RULES.get(name)
    if rule is None or _depth >= MAX_DEPTH:
        return None
    steps = []
    for sub_name, sub_params, sub_qargs in rule(list(params), list(qargs)):
        expanded = lower_steps(sub_name, sub_params, sub_qargs, has, _depth + 1)
        if expanded is None:
            return None
        steps.extend(expanded)
    return steps
