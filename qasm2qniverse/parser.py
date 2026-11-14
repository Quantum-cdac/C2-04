"""OpenQASM 2.0 / 3.0 (supported subset) parser producing the converter IR.

Supported subset is documented in docs/04-supported-constructs.md. Anything
outside the subset is reported as an unsupported statement with its line
number; parsing continues so the report covers the whole source.
"""

import ast
import re

from .errors import QasmSyntaxError
from .ir import CircuitIR, Operation, Register
from .report import ConversionReport

# QASM name -> (QSDK gate name, number of parameters, qubit arity).
# Only gates documented in the QSDK gate reference are listed.
GATE_MAP = {
    # single-qubit, no parameters
    "id": ("id", 0, 1), "x": ("x", 0, 1), "y": ("y", 0, 1), "z": ("z", 0, 1),
    "h": ("h", 0, 1), "s": ("s", 0, 1), "sdg": ("sdg", 0, 1),
    "t": ("t", 0, 1), "tdg": ("tdg", 0, 1),
    # single-qubit, parameterized
    "rx": ("rx", 1, 1), "ry": ("ry", 1, 1), "rz": ("rz", 1, 1),
    "u1": ("u1", 1, 1), "p": ("p", 1, 1),
    "u2": ("u2", 2, 1), "u3": ("u3", 3, 1), "u": ("u3", 3, 1),
    # two-qubit
    "cx": ("cx", 0, 2), "cnot": ("cx", 0, 2), "cy": ("cy", 0, 2),
    "cz": ("cz", 0, 2), "ch": ("ch", 0, 2), "swap": ("swap", 0, 2),
    "cs": ("cs", 0, 2), "ct": ("ct", 0, 2),
    "csdg": ("csdg", 0, 2), "ctdg": ("ctdg", 0, 2),
    "crx": ("crx", 1, 2), "cry": ("cry", 1, 2), "crz": ("crz", 1, 2),
    "cu1": ("cu1", 1, 2), "cp": ("cp", 1, 2),
    "cu2": ("cu2", 2, 2), "cu3": ("cu3", 3, 2),
    # multi-controlled
    "ccx": ("ccx", 0, 3), "cswap": ("cswap", 0, 3),
    "c3x": ("c3x", 0, 4), "c4x": ("c4x", 0, 5), "c5x": ("c5x", 0, 6),
}

# QSDK register names must be alphabetic and must not collide with gate names
# or Python keywords (per the QSDK "Creating a Circuit" documentation).
_RESERVED = set(GATE_MAP) | {"measure", "barrier", "reset"}

_HEADER_RE = re.compile(r"^\s*OPENQASM\s+(\d+(?:\.\d+)?)\s*$", re.IGNORECASE)
_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"


def _strip_comments(source):
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", source)


def _split_statements(source):
    """Split source into (statement, start_line) pairs on ';' and brace blocks."""
    statements = []
    buf = []
    depth = 0
    line = 1
    start_line = 1
    started = False
    for ch in source:
        if not started:
            if ch.isspace():
                if ch == "\n":
                    line += 1
                continue
            started = True
            start_line = line
        if ch == "\n":
            line += 1
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
            buf.append(ch)
            if depth == 0:
                text = "".join(buf).strip()
                if text:
                    statements.append((text, start_line))
                buf = []
                started = False
            continue
        if ch == ";" and depth == 0:
            text = "".join(buf).strip()
            if text:
                statements.append((text, start_line))
            buf = []
            started = False
            continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        statements.append((tail, start_line))
    return statements


def _eval_expr(expr, line, statement):
    """Evaluate a numeric parameter expression (numbers, pi, + - * /, parens)."""
    tree = ast.parse(expr.strip(), mode="eval")

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id == "pi":
            return 3.141592653589793
        if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)
        ):
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            return left / right
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = walk(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        raise QasmSyntaxError(
            "unsupported parameter expression %r" % expr, line=line, statement=statement
        )

    return walk(tree)


def _sanitize_name(name):
    """Make a QSDK-safe (alphabetic, non-reserved) register name, or None."""
    if re.fullmatch(r"[A-Za-z]+", name) and name not in _RESERVED:
        return None
    base = re.sub(r"[^A-Za-z]", "", name) or "reg"
    candidate = base
    while candidate in _RESERVED:
        candidate += "x"
    return candidate


class _Parser:
    def __init__(self, source, version=None):
        self.source = source
        self.forced_version = version
        self.report = ConversionReport()
        self.qregs = {}
        self.cregs = {}
        self.ir = CircuitIR(version="unknown")

    # -- helpers ----------------------------------------------------------
    def _wire(self, ref, registers, kind, line, statement):
        match = re.fullmatch(r"(%s)(?:\[(\d+)\])?" % _IDENT, ref.strip())
        if not match:
            raise QasmSyntaxError("invalid %s reference %r" % (kind, ref), line, statement)
        name, index = match.group(1), match.group(2)
        if name not in registers:
            raise QasmSyntaxError(
                "undeclared %s register %r" % (kind, name), line, statement
            )
        reg = registers[name]
        if index is None:
            return ("__whole__", name)
        idx = int(index)
        if idx < 0 or idx >= reg.size:
            raise QasmSyntaxError(
                "%s index %d out of range for register %r of size %d"
                % (kind, idx, name, reg.size),
                line,
                statement,
            )
        return (name, idx)

    def _expand_qargs(self, refs, arity, line, statement):
        """Resolve comma-separated qubit references, expanding whole registers."""
        resolved = [self._wire(r, self.qregs, "qubit", line, statement) for r in refs]
        wholes = [r for r in resolved if r[0] == "__whole__"]
        if not wholes:
            if len(resolved) != arity:
                raise QasmSyntaxError(
                    "gate expects %d qubit(s), got %d" % (arity, len(resolved)),
                    line,
                    statement,
                )
            return [resolved]
        sizes = {self.qregs[w[1]].size for w in wholes}
        if len(sizes) != 1:
            raise QasmSyntaxError(
                "register size mismatch in whole-register operation", line, statement
            )
        size = sizes.pop()
        expanded = []
        for i in range(size):
            group = []
            for r in resolved:
                group.append((r[1], i) if r[0] == "__whole__" else r)
            if len(group) != arity:
                raise QasmSyntaxError(
                    "gate expects %d qubit(s), got %d" % (arity, len(group)),
                    line,
                    statement,
                )
            expanded.append(group)
        return expanded

    # -- statement handlers -------------------------------------------------
    def _handle_declaration(self, stmt, line):
        patterns = [
            (r"^qreg\s+(%s)\[(\d+)\]$" % _IDENT, "q"),
            (r"^creg\s+(%s)\[(\d+)\]$" % _IDENT, "c"),
            (r"^qubit(?:\[(\d+)\])?\s+(%s)$" % _IDENT, "q3"),
            (r"^bit(?:\[(\d+)\])?\s+(%s)$" % _IDENT, "c3"),
        ]
        for pattern, kind in patterns:
            match = re.match(pattern, stmt)
            if not match:
                continue
            if kind in ("q", "c"):
                name, size = match.group(1), int(match.group(2))
            else:
                size = int(match.group(1)) if match.group(1) else 1
                name = match.group(2)
            registers = self.qregs if kind.startswith("q") else self.cregs
            if name in registers:
                raise QasmSyntaxError("duplicate register %r" % name, line, stmt)
            if size <= 0:
                raise QasmSyntaxError("register size must be positive", line, stmt)
            reg = Register(name=name, size=size, sdk_name=_sanitize_name(name))
            registers[name] = reg
            if kind.startswith("q"):
                self.ir.qregs.append(reg)
            else:
                self.ir.cregs.append(reg)
            if reg.sdk_name:
                self.report.warn(
                    "register %r renamed to %r: QSDK register names must be "
                    "alphabetic and not collide with gate or keyword names"
                    % (name, reg.sdk_name),
                    line,
                    stmt,
                )
            return True
        return False

    def _handle_measure(self, stmt, line):
        # 2.0: measure q[0] -> c[0];   3.0: c[0] = measure q[0]; / measure q -> c;
        match = re.match(r"^measure\s+(.+?)\s*->\s*(.+)$", stmt)
        if match:
            qref, cref = match.group(1), match.group(2)
        else:
            match = re.match(r"^(.+?)\s*=\s*measure\s+(.+)$", stmt)
            if not match:
                return False
            cref, qref = match.group(1), match.group(2)
        q = self._wire(qref, self.qregs, "qubit", line, stmt)
        c = self._wire(cref, self.cregs, "classical bit", line, stmt)
        # A bare single-wire register used against an indexed reference means
        # index 0 (QASM 3 style: `bit c; c = measure q[0];`).
        if q[0] == "__whole__" and self.qregs[q[1]].size == 1 and c[0] != "__whole__":
            q = (q[1], 0)
        if c[0] == "__whole__" and self.cregs[c[1]].size == 1 and q[0] != "__whole__":
            c = (c[1], 0)
        if q[0] == "__whole__" or c[0] == "__whole__":
            if q[0] != "__whole__" or c[0] != "__whole__":
                raise QasmSyntaxError(
                    "whole-register measurement needs register targets on both sides",
                    line,
                    stmt,
                )
            qreg, creg = self.qregs[q[1]], self.cregs[c[1]]
            if qreg.size != creg.size:
                raise QasmSyntaxError(
                    "register size mismatch in measurement", line, stmt
                )
            for i in range(qreg.size):
                self.ir.operations.append(
                    Operation("measure", qargs=[(qreg.name, i)],
                              cargs=[(creg.name, i)], line=line)
                )
            return True
        self.ir.operations.append(
            Operation("measure", qargs=[q], cargs=[c], line=line)
        )
        return True

    def _handle_barrier_or_reset(self, stmt, line):
        match = re.match(r"^(barrier|reset)\s*(.*?)$", stmt, re.DOTALL)
        if not match:
            return False
        kind, rest = match.group(1), match.group(2).strip()
        if kind == "barrier" and not rest:
            wires = self.ir.qubit_wires()
        else:
            refs = [r for r in rest.split(",") if r.strip()]
            wires = []
            for ref in refs:
                wire = self._wire(ref, self.qregs, "qubit", line, stmt)
                if wire[0] == "__whole__":
                    wires.extend((wire[1], i) for i in range(self.qregs[wire[1]].size))
                else:
                    wires.append(wire)
        self.ir.operations.append(Operation(kind, qargs=wires, line=line))
        return True

    def _handle_gate(self, stmt, line):
        match = re.match(
            r"^(%s)\s*(?:\((.*)\))?\s+(.+)$" % _IDENT, stmt, re.DOTALL
        )
        if not match:
            return False
        name = match.group(1).lower()
        if name not in GATE_MAP:
            return False
        sdk_name, nparams, arity = GATE_MAP[name]
        params = []
        if match.group(2) is not None:
            parts = [p for p in match.group(2).split(",") if p.strip()]
            params = [_eval_expr(p, line, stmt) for p in parts]
        if len(params) != nparams:
            raise QasmSyntaxError(
                "gate %r expects %d parameter(s), got %d" % (name, nparams, len(params)),
                line,
                stmt,
            )
        refs = [r for r in match.group(3).split(",") if r.strip()]
        for group in self._expand_qargs(refs, arity, line, stmt):
            self.ir.operations.append(
                Operation("gate", name=sdk_name, params=params, qargs=group, line=line)
            )
        return True

    # -- top level ----------------------------------------------------------
    def parse(self):
        statements = _split_statements(_strip_comments(self.source))
        if not statements:
            self.report.error("empty source")
            return self.ir, self.report

        first, first_line = statements[0]
        header = _HEADER_RE.match(first)
        if not header:
            raise QasmSyntaxError(
                "missing OPENQASM version header", line=first_line, statement=first
            )
        detected = header.group(1)
        major = detected.split(".")[0]
        if major not in ("2", "3"):
            raise QasmSyntaxError(
                "unsupported OpenQASM version %r" % detected, line=first_line
            )
        version = self.forced_version or ("2.0" if major == "2" else "3.0")
        if self.forced_version and self.forced_version.split(".")[0] != major:
            self.report.warn(
                "caller-forced version %s overrides detected header %s"
                % (self.forced_version, detected),
                first_line,
                first,
            )
        self.ir.version = version
        self.report.detected_version = detected

        for stmt, line in statements[1:]:
            head = stmt.split(None, 1)[0] if stmt.split() else ""
            try:
                if re.match(r"^include\s", stmt):
                    continue  # qelib1.inc / stdgates.inc: recognised, no-op
                if re.match(r"^(gate|opaque)\b", stmt) or "{" in stmt:
                    self.report.unsupported(
                        "custom gate definitions and composite blocks are outside "
                        "the supported subset",
                        line,
                        stmt.split("{")[0].strip() + " {...}",
                    )
                    continue
                if re.match(r"^(if|for|while|def|extern|const|let|input|output)\b", head):
                    self.report.unsupported(
                        "dynamic/classical construct %r is outside the supported subset"
                        % head,
                        line,
                        stmt,
                    )
                    continue
                if self._handle_declaration(stmt, line):
                    continue
                if self._handle_measure(stmt, line):
                    continue
                if self._handle_barrier_or_reset(stmt, line):
                    continue
                if self._handle_gate(stmt, line):
                    continue
                name = head.split("(")[0].strip()
                if re.fullmatch(_IDENT, name):
                    self.report.unsupported(
                        "gate %r is not in the supported QSDK gate subset" % name,
                        line,
                        stmt,
                    )
                else:
                    self.report.unsupported("unrecognised statement", line, stmt)
            except QasmSyntaxError as exc:
                self.report.error(str(exc), line=exc.line or line, statement=stmt)
                raise

        self.report.mapped_operations = len(self.ir.operations)
        self.report.quantum_registers = [
            {"name": r.name, "size": r.size, "sdk_name": r.effective_sdk_name}
            for r in self.ir.qregs
        ]
        self.report.classical_registers = [
            {"name": r.name, "size": r.size, "sdk_name": r.effective_sdk_name}
            for r in self.ir.cregs
        ]
        if not self.ir.qregs and self.report.status != "failed":
            self.report.error("no quantum register declared")
        return self.ir, self.report


def parse_qasm(source, version=None):
    """Parse an OpenQASM 2.0/3.0 source string into the converter IR.

    Args:
        source: QASM program as a string.
        version: optional "2.0"/"3.0" override; otherwise taken from the header.

    Returns:
        (CircuitIR, ConversionReport).

    Raises:
        QasmSyntaxError: on fatal syntax errors (after recording them in the
            report, which is attached as ``exc.report``).
    """
    parser = _Parser(source, version=version)
    try:
        return parser.parse()
    except QasmSyntaxError as exc:
        if not parser.report.errors:
            parser.report.error(str(exc), line=exc.line, statement=exc.statement)
        exc.report = parser.report
        raise
