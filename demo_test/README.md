# C2-04 demo cases

28 QASM cases + expected results, run through the C2-04 parser and its reference simulator.

## Run (Qniverse notebook cell)
```python
!git clone https://github.com/Quantum-cdac/C2-04.git   # once
!git -C C2-04 pull --ff-only                            # to update
!python -m pytest C2-04/tests -q                        # repo's own tests
!python demo_test/run_demo.py C2-04                    # these cases
```
Output: PASS/FAIL per case, plus `results.md` and `results.json`.
Edit cases in `make_cases.py`, then `python make_cases.py` to regenerate.

## Layout
- `cases/*.qasm`: one file per case (paste any into the Qniverse QASM panel)
- `manifest.json`: category, why it exists, expected distribution (c[n-1]..c[0]) or "must reject"
- `run_demo.py`: runner, tolerance 1e-9
- `results.md`: last run

## Categories
- A-sanity (01-02): does it work at all
- B-scope (03-12): what is supported, and unsupported constructs that must be reported with a line number
- C-boundary (13-28): bit order, max index, Toffoli truth table, angle edges, formatting, invalid input

## Last run: 25/28 passed. The 3 FAILs are real parser gaps, kept visible on purpose
| Case | Behaviour found | Why it matters |
|---|---|---|
| 23_missing_semicolon | `h q[0]` with no final `;` is accepted, status=success | Silent leniency on malformed input |
| 25_cx_same_qubit | `cx q[0], q[0]` accepted, status=success | Invalid gate passes the parser; the simulator would only fail later |
| 26_divide_by_zero | `rz(1/0)` raises a raw `ZeroDivisionError` | Loud, but not a structured report with a line number |

Say these to sir as known limitations, or tell Priyans to fix them. Either is better than being caught by them.

## Not proven here
- Nothing in this folder ran on Qniverse. Results are against the repo's own simulator.
- The Qniverse QSDK is not installed here, so `tests/test_qniverse_integration.py` is skipped and no QniverseCircuit was built.
- These cases test Priyans' `qasm2qniverse`, not your own `qasm2ir`/`backend`.
