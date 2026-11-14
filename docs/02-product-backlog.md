# 02 - Product Backlog (Agile SDLC)

Event format: 9-hour hackathon with judged checkpoints at ~3h (Mid Evaluation I, at least one working problem) and ~6h (Mid Evaluation II, a second problem). This backlog is ordered so a demonstrable converter exists early and depth is added incrementally.

## Sprint 0 - Foundations (hour 0-1)

- [x] PB-1 Repository, package skeleton, README, requirements
- [x] PB-2 Environment check: `pip install qniverse` / Qniverse JupyterLab access, `QniverseCircuit.list_gates()` to confirm the documented gate catalog on the venue SDK build

## Sprint 1 - Walking skeleton (target: demo-ready by Mid Evaluation I)

- [x] PB-3 IR (`CircuitIR`, registers, operations) and conversion report schema
- [x] PB-4 QASM 2.0 parser: header, `qreg`/`creg`, core gates, `measure ... -> ...`
- [x] PB-5 QSDK builder: IR -> `QniverseCircuit` via documented interfaces only
- [x] PB-6 Smoke demo: Bell pair in, conversion report + circuit out (`demo.py`)

## Sprint 2 - Breadth and correctness

- [x] PB-7 QASM 3.0 surface syntax (`qubit[n] q`, `bit[n] c`, `c = measure q`, `U`, `p`)
- [x] PB-8 Parameterized gates and expression evaluation (`pi`, arithmetic)
- [x] PB-9 Whole-register operations, barrier, reset, multi-register programs
- [x] PB-10 Diagnostics: unknown gates, bad indices, malformed source, unsupported constructs, with line numbers
- [x] PB-11 Register-name sanitization for QSDK naming rules, with warnings

## Sprint 3 - Evidence and hardening

- [x] PB-12 Reference statevector simulator; equivalence tests (Bell, GHZ, rotations, swap, Toffoli, controlled-phase)
- [x] PB-13 Integration tests against the real SDK incl. round-trip via documented `qc.qasm()` export (run in Qniverse JupyterLab)
- [ ] PB-14 Execute converted circuits on a Qniverse simulator backend and attach measurement distributions (needs event API key; venue step)
- [ ] PB-15 Organizer confirmation of any subset-boundary questions raised at the access briefing

## Definition of done

Unit + equivalence tests green, demo reproducible from README, docs updated, and every claim in the docs traceable to a test or a documented SDK page.
