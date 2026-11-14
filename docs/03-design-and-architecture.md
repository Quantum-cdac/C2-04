# 03 - Design and Architecture (Technical Approach)

## Pipeline

```
QASM source string
      |
      v
[parser.py]  version detect -> tokenize -> statements -> IR
      |            (QASM 2.0 and 3.0 share one IR)
      v
CircuitIR  +  ConversionReport
      |
      +--> [builder.py]  IR -> QniverseCircuit   (documented QSDK APIs only)
      |
      +--> [simulator.py] IR -> statevector      (offline equivalence evidence)
```

Three deliberate separations:

1. **Parser never imports the SDK.** Parsing, validation, diagnostics and the conversion report are SDK-independent, so they are testable anywhere and cannot accidentally rely on undocumented SDK behavior.
2. **One thin SDK adapter.** `builder.py` is the only module that imports `Qniverse`. Every SDK call in it appears in the QSDK documentation (see References). If the venue SDK build differs, only this file changes.
3. **Independent reference simulator.** `simulator.py` computes statevectors straight from the IR with its own gate matrices. It shares no code with the builder, so equivalence tests compare two independent readings of the same semantics.

## Key design decisions

- **Common string-based interface** (FR1): `convert_qasm(source, version=None)`. Version is taken from the `OPENQASM` header; a caller-supplied version overrides it and is recorded as a warning when it disagrees with the header.
- **IR preserves semantics before any SDK call** (FR4): registers keep declaration order; operations keep source order; parameters are evaluated once to floats; qubit references stay as `(register, index)` pairs, so register ordering and qubit indices are preserved by construction.
- **QSDK naming rules handled explicitly**: QSDK register names must be alphabetic and must not collide with gate or keyword names. Non-conforming QASM register names (e.g. `q_1`) are mapped to a safe name (`q`) and the rename is reported as a warning, not silently applied.
- **Strict by default, explicit partial mode**: unsupported statements are always collected with line numbers and reasons, and parsing continues so the report covers the whole source. But because dropping a statement (for example an `if`-conditioned gate) can change the quantum semantics of the program, `convert_qasm` does not return an executable circuit for a partially-converted source unless the caller passes `allow_partial=True` (a diagnostics-only build, marked with a warning in the report). This matches the problem statement: the report must carry "conversion status, warnings and unsupported statements", and the converter must "preserve the semantics of every accepted operation" - a strict default is what keeps a partial program from masquerading as an equivalent circuit. Status is `success` / `partial` / `failed`; fatal syntax errors raise `QasmSyntaxError` with the partial report attached.
- **Whole-register operations follow QASM semantics**: `h q;` over a 2-qubit register expands to one gate per qubit; `measure q -> c;` expands pairwise and requires equal sizes; mixed whole/index forms are allowed only for single-wire registers (QASM 3 `bit c; c = measure q[0];`).

## Mathematical concepts used

- Gate semantics follow the standard matrices: Pauli gates, Hadamard, phase gates `s/t` and adjoints, rotations `rx/ry/rz(theta)`, Euler decomposition `u3(theta, phi, lambda)` with `u1(lambda) = diag(1, e^{i lambda})`, `u2(phi, lambda) = u3(pi/2, phi, lambda)`, and controlled versions `U_c = |0><0> (x) I + |1><1> (x) U` (extended to `ccx/c3x/c4x/c5x/cswap`).
- Equivalence evidence uses the statevector model: a circuit is a sequence of unitary applications on `C^(2^n)`; two programs are equivalent for the tested examples when their statevectors match up to machine precision (fidelity 1) or, where a global phase is expected (`rx(pi)` vs `x`), when their measurement distributions match.

## References

- QSDK documentation - Getting Started: https://qniverse.in/docs-category/qsdk/introduction/getting_started.html
- QSDK documentation - Creating a Circuit (registers, `add_register`, `add_gate`, measurement, conditional gates): https://qniverse.in/docs-category/qsdk/introduction/creating_a_circuit.html
- QSDK documentation - Quantum Gates (documented gate catalog used for the mapping): https://qniverse.in/docs-category/qsdk/gates_and_modules/gates.html
- OpenQASM 2.0 specification: A. W. Cross et al., "OpenQASM 2.0: A broader and deeper quantum assembly language", arXiv:1707.03429
- OpenQASM 3.0 specification: A. W. Cross et al., "OpenQASM 3: A broader and deeper quantum assembly language", arXiv:2104.14722
