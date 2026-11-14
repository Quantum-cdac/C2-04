# 05 - Test Plan and Results

## Layout

| Suite | File | Needs QSDK? | Covers |
|---|---|---|---|
| Parser correctness | `tests/test_parser.py` | no | version detect/override, structure preservation, parameter expressions, multi-register programs, whole-register expansion, barrier defaults, rename warnings |
| Strict policy | `tests/test_strict_policy.py` | no | partial sources raise by default (no executable circuit); explicit `allow_partial=True` build is marked in the report |
| Diagnostics | `tests/test_diagnostics.py` | no | missing header, unknown gates (with line numbers), custom gate definitions, dynamic constructs, invalid indices, undeclared registers, wrong parameter counts, symbolic parameters |
| Equivalence | `tests/test_equivalence.py` | no | statevector checks: Bell (analytic), QASM2 vs QASM3 spellings, GHZ, `rx(pi)` vs `x` distributions, swap, Toffoli, controlled phase, measure/barrier transparency |
| Decomposition | `tests/test_lowering.py` | no | every lowering rule's unitary matches the native gate up to global phase (permuted operand orders included); builder fallback against a fake SDK missing `ccx`/`cp`/`crz` converts with per-gate warnings and phase-equivalent output |
| SDK integration | `tests/test_qniverse_integration.py` | yes | real `QniverseCircuit` construction, round-trip through the documented `qc.qasm()` export re-parsed and re-simulated (Bell and a parameterized program - validates the actual builder output, not just import success) |

Run everything:

```
pip install -r requirements.txt
python -m pytest tests/ -q
```

## Results (this workspace, 2026-11-14)

```
49 passed, 1 skipped in 0.09s
```

(Second run of the day, after the decomposition fallback and its suite were added; the earlier run read `27 passed, 1 skipped in 0.09s`. The integration suite also passes against a test double of the venue SDK build, 5 passed, including the multi-register QASM 3.0 round trip added the same day.)

- The skip is `tests/test_qniverse_integration.py`: the Qniverse QSDK is not installed in this development environment, and the suite skips itself via `pytest.importorskip` rather than faking a pass. Note: `pip install qniverse` failed in this development environment with "No matching distribution" and https://pypi.org/pypi/qniverse/json returns HTTP 404 (checked 2026-11-14, ~10:13 IST), although the official Getting Started page documents pip installation. Verified on the venue the same day: the Qniverse Jupyter Notebook has the SDK preinstalled as lowercase `qniverse` (class `qniverse.QniverseCircuit.QniverseCircuit`; `add_register(register)`, `add_gate(gate, *indices)`, `qasm(shots=None)` match the documented uppercase API). The builder and the integration suite resolve either package casing, so the suite runs in that notebook without changes. One behavioral difference was found in the venue build and handled: `QniverseCircuit.qasm()` prints the program and returns `None` there, so the converter exposes `export_qasm(circuit)`, which returns the string when the SDK returns one and captures stdout otherwise; the integration tests use it.
- Run the integration suite where the SDK is available (for example the Qniverse Jupyter Notebook, see below): `python -m pytest tests/test_qniverse_integration.py -q`. If pytest is absent there (the documented notebook image lists Qiskit/NumPy but not pytest), either `!pip install pytest` in a cell or fall back to `python demo.py`, which needs only the standard library plus NumPy. Its results belong in this file once executed at the venue.

## Results (venue Qniverse Jupyter Notebook, 2026-11-14, ~11:07-11:11 IST)

Executed by the team in the per-user Qniverse notebook against the preinstalled lowercase `qniverse` SDK:

```
$ python -m pytest tests/test_qniverse_integration.py -q
....                                                                     [100%]
4 passed in 1.09s
```

The SDK-gated suite passes at the venue: Bell build + documented-`qasm()` round trip, and the parameterized (rx/crz/u3) round trip with statevector fidelity 1.0. A manual Bell conversion run in the same notebook printed `status: success`, `circuit: QniverseCircuit`, a clean re-parse of the exported QASM (`reparse errors: []`) and `statevector fidelity: 0.9999999999999996` (1.0 within float precision).

## Results (venue Qniverse Jupyter Notebook, 2026-11-14, ~11:28 IST, commit 941aba2)

Full suite on the strengthened build, executed by the team in the same venue notebook:

```
......................................................                   [100%]
54 passed in 1.06s
```

This run includes all five SDK integration tests against the real installed `qniverse` package - Bell build, documented-`qasm()` round trip, parameterized build, parameterized round trip, and the multi-register QASM 3.0 build + round trip (`test_multiregister_qasm3_build_and_round_trip`: two quantum registers, cross-register `cx`, pairwise measurement, fidelity 1.0 through the documented export) - plus the 49 offline tests (parser, diagnostics, strict policy, equivalence, decomposition rules, builder fallback).

## Remote platform job: converter output executed on QACC_Cluster (2026-11-14, 11:41 IST)

Job **37982**, submitted through the Qniverse web composer by the team, ran this converter's exported QASM for `examples/bell_qasm2.qasm` (commit `22d1113`): resource `QACC_Cluster-CPU`, simulator `qasm_simulator`, noise off, 1024 shots, status **COMPLETED**.

Result (`output.txt` from the platform's per-job export):

```json
{"probability": {"11": 518, "00": 506}, "shots": 1024}
```

This is the Bell-consistent distribution the PS's "compare measurement distributions of source and converted circuits" item asks for, now produced by the platform itself on the converted circuit.

Provenance evidence: the job's exported `qasm_code.txt` matches this converter's `export_qasm` output for the example exactly apart from whitespace after commas (the composer re-serializes pasted input), and it contains the per-qubit expanded barrier (`barrier q[0], q[1];`) that this converter's export produces, which the raw example file (`barrier q;`) does not. This is consistency evidence, not a cryptographic trace. The job's other exported artifacts: `circuitImage.png`, `HistogramImage.png`, `photonicCircuitImage.png`.

Cost observed: the account credit counter shown in the platform UI went from 150 (hackathon allocation) to 145 for this run - consistent with the dated 5-credits-per-CPU-simulation release note, and recorded here as the current observed charge.

Separately observed on the platform the same day (teammate's account): a circuit job on the QACC_Cluster-CPU `qasm_simulator` (1024 shots, no noise) completed with the expected ~50/50 000/111 distribution, confirming platform job submission works at the venue. That job ran a hand-built circuit, not this converter's output; a converter-output platform run is optional additional evidence and carries a credit cost - the Qniverse release notes (v1.2.0, 04-Jul-2025, https://qniverse.in/release-notes/) document 5 credits per CPU simulation; the live balance can be checked with the documented `credit_balance()` job API before running.

## Equivalence method

The reference simulator (`qasm2qniverse/simulator.py`) computes statevectors from the IR with independently written gate matrices. Two comparisons are used:

1. IR -> statevector vs the known analytic state (Bell, GHZ).
2. IR -> statevector vs a re-parse of the circuit's documented QASM export (`qc.qasm()`), fidelity 1.0 - integration suite.

Convention: wire 0 (first declared) is the least significant bit of the basis index; controlled-gate matrices take the last target wire as the target, matching the documented QSDK convention.

Scope of this evidence: these are checks on representative programs, not a proof of semantic preservation for every accepted input. Statevector fidelity on fixed inputs demonstrates agreement on those inputs; it does not by itself establish equality of the full unitaries or of measurement semantics in general (the decomposition suite closes part of that gap at the unitary level for the lowering rules). Bell and GHZ states are symmetric under bit relabeling, so they cannot detect a bit-order mismatch against the SDK; the documented wire convention is verified against the SDK's documented behavior, and a dedicated asymmetric check (for example `x` on one wire of a multi-qubit register, then read the exported QASM/histogram) remains the way to pin the platform's bit order empirically.

## Error-handling evidence

`examples/unsupported_constructs.qasm` (run via `python demo.py`) produces a `partial` report listing all four unsupported statements with line numbers (custom gate definition, its use, `if`, `for`) while still converting the supported remainder.

## Venue run path (Qniverse Jupyter Notebook)

The platform gives each user an isolated Jupyter Notebook (side panel -> Launch Notebook; documented at https://qniverse.in/docs/qniverse-labs-resources/). The docs list Python 3.9.13 / NumPy 1.26.4 / Qiskit 1.1.1; the image observed on 2026-11-14 was a conda Python 3.11 with the lowercase `qniverse` SDK preinstalled. The codebase is parse-verified compatible with Python 3.9 through 3.11 (stdlib + NumPy only; `ast.parse` audit at feature_version=(3,9) passes on every shipped module). Steps that were executed there: `git clone` this repository, `!pip install pytest` (not in the image), then `python -m pytest tests/ -q`. `python demo.py` needs only the standard library plus NumPy.
