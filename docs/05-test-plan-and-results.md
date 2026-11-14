# 05 - Test Plan and Results

## Layout

| Suite | File | Needs QSDK? | Covers |
|---|---|---|---|
| Parser correctness | `tests/test_parser.py` | no | version detect/override, structure preservation, parameter expressions, multi-register programs, whole-register expansion, barrier defaults, rename warnings |
| Strict policy | `tests/test_strict_policy.py` | no | partial sources raise by default (no executable circuit); explicit `allow_partial=True` build is marked in the report |
| Diagnostics | `tests/test_diagnostics.py` | no | missing header, unknown gates (with line numbers), custom gate definitions, dynamic constructs, invalid indices, undeclared registers, wrong parameter counts, symbolic parameters |
| Equivalence | `tests/test_equivalence.py` | no | statevector checks: Bell (analytic), QASM2 vs QASM3 spellings, GHZ, `rx(pi)` vs `x` distributions, swap, Toffoli, controlled phase, measure/barrier transparency |
| SDK integration | `tests/test_qniverse_integration.py` | yes | real `QniverseCircuit` construction, round-trip through the documented `qc.qasm()` export re-parsed and re-simulated (Bell and a parameterized program - validates the actual builder output, not just import success) |

Run everything:

```
pip install -r requirements.txt
python -m pytest tests/ -q
```

## Results (this workspace, 2026-11-14)

```
27 passed, 1 skipped in 0.09s
```

- The skip is `tests/test_qniverse_integration.py`: the Qniverse QSDK is not installed in this development environment, and the suite skips itself via `pytest.importorskip` rather than faking a pass. Note: `pip install qniverse` failed here with "No matching distribution" and https://pypi.org/pypi/qniverse/json returns HTTP 404 (checked 2026-11-14, ~10:13 IST), although the official Getting Started page documents pip installation. SDK availability therefore needs confirming at the venue (Qniverse JupyterLab or an organizer-provided index); the integration suite is ready to run the moment the SDK is present.
- Run the integration suite where the SDK is available (for example the Qniverse Jupyter Notebook, see below): `python -m pytest tests/test_qniverse_integration.py -q`. If pytest is absent there (the documented notebook image lists Qiskit/NumPy but not pytest), either `!pip install pytest` in a cell or fall back to `python demo.py`, which needs only the standard library plus NumPy. Its results belong in this file once executed at the venue.

## Equivalence method

The reference simulator (`qasm2qniverse/simulator.py`) computes statevectors from the IR with independently written gate matrices. Two comparisons are used:

1. IR -> statevector vs the known analytic state (Bell, GHZ).
2. IR -> statevector vs a re-parse of the circuit's documented QASM export (`qc.qasm()`), fidelity 1.0 - integration suite.

Convention: wire 0 (first declared) is the least significant bit of the basis index; controlled-gate matrices take the last target wire as the target, matching the QSDK convention.

## Error-handling evidence

`examples/unsupported_constructs.qasm` (run via `python demo.py`) produces a `partial` report listing all four unsupported statements with line numbers (custom gate definition, its use, `if`, `for`) while still converting the supported remainder.

## Venue run path (Qniverse Jupyter Notebook)

The platform gives each user an isolated Jupyter Notebook (side panel -> Launch Notebook; documented at https://qniverse.in/docs/qniverse-labs-resources/): Python 3.9.13, NumPy 1.26.4, Qiskit 1.1.1, 4 GB RAM. The codebase is verified compatible with Python 3.9 (stdlib + NumPy only; `ast.parse` audit at feature_version=(3,9) passes on every shipped module). Steps: upload or clone this repository, run `python demo.py`, then `python -m pytest tests/ -q` (or the integration file alone once `import Qniverse` works in that environment).
