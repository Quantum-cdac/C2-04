# 01 - Requirements

Problem: **QC-C2-04 - OpenQASM 2.0/3.0 to QniverseCircuit Converter** (Class II, environment: Qniverse / QSDK where supported).

## Objective (from the problem statement)

Develop a converter that accepts OpenQASM 2.0 or OpenQASM 3.0 source code as a string and returns an equivalent `QniverseCircuit` object using documented Qniverse QSDK interfaces. The converter supports a defined subset of QASM constructs and preserves the semantics of every accepted operation.

## Functional requirements (mandatory, from the problem statement)

| # | Requirement | Where met |
|---|---|---|
| FR1 | Callable function accepting a QASM source string; language version (2.0/3.0) detected or given | `qasm2qniverse.convert_qasm(source, version=None)`; header detection with optional caller override |
| FR2 | Parse supported quantum/classical register declarations, standard gates, parameterized gates, barriers and measurements | `qasm2qniverse/parser.py`; supported set in `docs/04-supported-constructs.md` |
| FR3 | Create the `QniverseCircuit` through documented QSDK interfaces only | `qasm2qniverse/builder.py` (single SDK touchpoint; uses `QniverseCircuit()`, `QuantumRegister`, `ClassicalRegister`, `add_register`, `add_gate`, `Qniverse.gates`) |
| FR4 | Preserve qubit indices, register ordering, gate parameters, operation order and measurement mappings | IR keeps declaration order and source order; tests in `tests/test_parser.py`, `tests/test_equivalence.py` |
| FR5 | Return the circuit with conversion status, warnings and unsupported statements | `ConversionReport` (status / mapped_operations / warnings / unsupported_statements / errors); strict default refuses an executable circuit for partial sources, `allow_partial=True` gives an explicitly marked diagnostics-only build |

## Correctness tests (from the problem statement)

- Representative QASM 2.0 and 3.0 programs with single- and multi-qubit gates - `tests/test_equivalence.py`, `examples/`
- Parameterized rotations, multiple registers, barriers and measurements - `tests/test_parser.py`, `tests/test_equivalence.py`
- Statevector comparison of source and converted circuits for small examples - reference simulator in `qasm2qniverse/simulator.py`; round-trip through the documented `QniverseCircuit.qasm()` export in `tests/test_qniverse_integration.py`
- Malformed source, unknown gates, invalid indices, unsupported dynamic constructs - `tests/test_diagnostics.py`

## Non-functional requirements

- **Zero-cost tooling**: pure Python + numpy + pytest; no paid services.
- **No undocumented SDK usage**: only interfaces shown in the QSDK documentation (see References in `docs/03-design-and-architecture.md`).
- **Actionable diagnostics**: every rejected statement is reported with a line number and reason; parsing continues past unsupported statements.
- **Honest reporting**: no fabricated benchmarks; integration tests skip (not pass) when the SDK is absent.

## Out of scope (declared subset boundary)

Custom `gate`/`opaque` definitions, dynamic circuits (`if`/loops on classical values), classical arithmetic, non-constant parameter symbols, and gates without a documented QSDK counterpart (for example `sx`). Full list: `docs/04-supported-constructs.md`.
