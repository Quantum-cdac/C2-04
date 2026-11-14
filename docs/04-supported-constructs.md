# 04 - Supported Constructs and Gate Mappings

Everything not listed here is rejected with an `unsupported` report entry that carries the statement's line number and reason. A source with any unsupported statement yields no executable circuit by default (strict mode); `allow_partial=True` produces a diagnostics-only build of the accepted remainder, explicitly marked in the report.

## Structure

| Construct | OpenQASM 2.0 | OpenQASM 3.0 |
|---|---|---|
| Version header | `OPENQASM 2.0;` | `OPENQASM 3.0;` / `OPENQASM 3;` |
| Standard include | `include "qelib1.inc";` | `include "stdgates.inc";` (recognised, no-op) |
| Quantum register | `qreg q[3];` | `qubit[3] q;`, `qubit q;` |
| Classical register | `creg c[3];` | `bit[3] c;`, `bit c;` |
| Measurement | `measure q[0] -> c[0];`, `measure q -> c;` | `c[0] = measure q[0];`, `c = measure q;`, `measure q -> c;` |
| Barrier | `barrier q;`, `barrier q[0],q[1];`, `barrier;` | same forms |
| Reset | `reset q[0];`, `reset q;` | same forms |
| Parameters | numbers, `pi`, `+ - * /`, parentheses, unary minus | same |

Whole-register gate application (`h q;`) expands element-wise; binary gates over two whole registers expand pairwise and require equal sizes.

## Gate mapping (QASM -> QSDK `Qniverse.gates`)

| QASM | QSDK | Parameters |
|---|---|---|
| `id`, `x`, `y`, `z`, `h`, `s`, `sdg`, `t`, `tdg` | same names | - |
| `rx`, `ry`, `rz` | same names | `theta` |
| `u1(l)`, `p(l)` | `u1`, `p` | `lambda` |
| `u2(p,l)` | `u2` | `phi, lambda` |
| `u3(t,p,l)`, `u(t,p,l)` / `U` | `u3` | `theta, phi, lambda` |
| `cx`, `CX`, `cnot` | `cx` | - |
| `cy`, `cz`, `ch`, `swap` | same names | - |
| `cs`, `ct`, `csdg`, `ctdg` | same names | - |
| `crx`, `cry`, `crz` | same names | `theta` |
| `cu1`, `cp` | `cu1`, `cp` | `lambda` |
| `cu2`, `cu3` | same names | per gate |
| `ccx`, `cswap` | same names | - |
| `c3x`, `c4x`, `c5x` | same names | - |
| `measure` | `measure` (qubit + clbit) | - |
| `barrier`, `reset` | `barrier`, `reset` | - |

Qubit order convention matches the QSDK documentation: the last argument is the target for controlled gates.

## Explicitly unsupported (reported, not silently dropped)

- Custom gate definitions (`gate name ... { ... }`) and `opaque` declarations, and any use of such gates
- Dynamic circuits: `if` on classical values, `for`/`while` loops
- Classical declarations and arithmetic (`const`, `let`, `int`, ...), `extern`, `def`, `input`/`output`
- Symbolic (non-constant) gate parameters, e.g. `rx(theta)`
- Gates without a documented QSDK counterpart, e.g. `sx`, `sxdg`, `gphase`, `ecr`
- Register names that violate QSDK naming rules are auto-renamed with a warning rather than rejected (see `docs/03-design-and-architecture.md`)

## Register naming

QSDK register names must be alphabetic, unique per circuit, and must not collide with gate or Python keyword names. The converter maps offending names to a safe alphabetic form (recorded in the report as a warning with old and new names); wire indices are unchanged.

## Decomposition fallback (installed-SDK gate gaps)

The builder always prefers the native QSDK gate. When the installed SDK build does not expose a mapped gate, `qasm2qniverse/lowering.py` substitutes a standard decomposition instead of failing: `ccx`, `cswap`, `cy`, `cz`, `ch`, `swap`, `crz`, `cp`/`cu1`, `cs`/`ct`/`csdg`/`ctdg`, `crx`, `cry`, `cu2`, `cu3`, and the phase-gate chain `u1`/`p`/`s`/`sdg`/`t`/`tdg`/`u2`/`u3`. Every substitution is recorded in the report as a warning with the source line. Rules are exact unitaries except where marked up to global phase (`p`->`rz`, `u3`->`rz/ry/rz` chain); a global phase never changes a measurement distribution. `tests/test_lowering.py` proves each rule against the reference simulator's matrices, including permuted operand orders. `c3x`/`c4x`/`c5x` have no ancilla-free rule: if the SDK lacks them, conversion raises a clear error rather than guessing. The rule set follows standard references and was cross-validated against a teammate's independent implementation of the same decompositions.
