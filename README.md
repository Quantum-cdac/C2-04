# QC-C2-04 - OpenQASM 2.0/3.0 to QniverseCircuit Converter

Converts an OpenQASM 2.0 or 3.0 program (supplied as a string) into an equivalent `QniverseCircuit` built through documented Qniverse QSDK interfaces, and returns a structured conversion report: detected version, mapped operations, warnings and unsupported statements with line numbers.

## Quick start

```bash
pip install -r requirements.txt
python demo.py                 # converts examples/ and prints reports
python -m pytest tests/ -q     # 24 offline tests; SDK suite self-skips
```

```python
from qasm2qniverse import convert_qasm

result = convert_qasm(source)      # version auto-detected
result.circuit                     # QniverseCircuit
result.report.to_dict()            # status / warnings / unsupported / errors
```

Building circuits needs the Qniverse QSDK (`pip install qniverse` per the official docs, or the Qniverse Jupyter Notebook where it is preinstalled as the lowercase `qniverse` package - both casings are accepted). Parsing, diagnostics and the equivalence tests run without it.

## Repository layout

- `qasm2qniverse/` - package: `parser.py` (QASM 2.0/3.0 subset -> IR), `builder.py` (IR -> `QniverseCircuit`, documented QSDK APIs only), `simulator.py` (reference statevector engine for equivalence tests), `report.py`, `ir.py`, `errors.py`
- `tests/` - parser, diagnostics, equivalence and QSDK integration suites
- `examples/` - runnable QASM 2.0/3.0 samples incl. an unsupported-constructs showcase
- `docs/` - SDLC and submission documents (requirements, backlog, design, supported constructs, test results, performance analysis, product documentation, AI-usage disclosure, team info)

## Documentation map

| Doc | Content |
|---|---|
| `docs/01-requirements.md` | problem requirements and where each is met |
| `docs/02-product-backlog.md` | agile backlog and definition of done |
| `docs/03-design-and-architecture.md` | technical approach, math concepts, references |
| `docs/04-supported-constructs.md` | supported subset and QASM -> QSDK gate mapping |
| `docs/05-test-plan-and-results.md` | test plan, results, equivalence method |
| `docs/06-performance-analysis.md` | complexity and resource analysis |
| `docs/07-product-documentation.md` | install, usage, I/O, workflow, limitations |
| `docs/08-ai-usage-disclosure.md` | material AI-tool use disclosure (per hackathon rules) |
| `docs/00-team-information.md` | team details (fill before submission) |
