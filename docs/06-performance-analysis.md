# 06 - Performance and Resource Analysis

Scope: the converter is a compile-time tool, so the analysis covers parsing/build cost and the cost of the validation evidence, not circuit execution (which belongs to the Qniverse backend that runs the converted circuit).

## Time complexity

| Stage | Cost | Notes |
|---|---|---|
| Statement split | O(L) in source length L | single scan |
| Parse per statement | O(L) total | regex per statement; whole-register expansion adds O(n_gates * max_register_size) output operations |
| Parameter evaluation | O(1) per parameter | constant arithmetic expressions only |
| IR -> QniverseCircuit build | O(G) in expanded gate count G | one documented `add_gate` call per operation |
| Reference simulation (tests only) | O(G * 4^n) time, O(2^n) memory for n qubits | dense statevector; used for small examples only |

## Resource usage of converted circuits

The converter preserves the source program's resources by construction and reports them in the IR/report:

- **Qubits**: sum of declared `qreg`/`qubit` sizes (no ancillas added by conversion).
- **Classical bits**: sum of declared `creg`/`bit` sizes.
- **Gate count / depth**: operations map 1:1 into the `QniverseCircuit` (except whole-register expansion, which is the QASM semantics, not overhead), so circuit depth and gate counts of the generated circuit equal those of the source program restricted to the supported subset.

Measured on the shipped examples (this workspace, 2026-11-14): parse+report for all five example programs completes in well under 100 ms total (`python demo.py`); the full offline test suite (24 tests) runs in ~0.06 s. These are wall-clock observations on the development container, not benchmarks; no remote-execution numbers are claimed here.

## Limits to state plainly

- The reference simulator is exponential in qubit count; it is a correctness oracle for small examples, not a scalable simulator.
- Conversion cost is dominated by the source size and register widths of whole-register operations; both are linear in the expanded program.
