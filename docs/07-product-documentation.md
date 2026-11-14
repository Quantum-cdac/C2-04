# 07 - Product Documentation

## Purpose

`qasm2qniverse` converts an OpenQASM 2.0 or 3.0 program, supplied as a string, into an equivalent `QniverseCircuit` object built through documented Qniverse QSDK interfaces, plus a structured conversion report (detected version, mapped operations, warnings, unsupported statements).

## Installation

```
pip install -r requirements.txt   # numpy + pytest
pip install qniverse              # Qniverse QSDK, needed to build circuits
```

Python 3.8+. Inside the Qniverse JupyterLab the SDK is already available and only the first line is needed. No API key is needed to convert or to run the offline tests; remote execution on Qniverse backends uses the account API key from https://qniverse.in (profile dashboard) and is not part of conversion.

## Running in the Qniverse Jupyter Notebook

The platform's per-user Jupyter Notebook (side panel -> Launch Notebook; https://qniverse.in/docs/qniverse-labs-resources/) has the QSDK preinstalled as the lowercase package `qniverse` (verified in that notebook on 2026-11-14: the class is `qniverse.QniverseCircuit.QniverseCircuit`, gates are re-exported at package top level, and the image observed was a conda Python 3.11 rather than the documented 3.9.13 - the converter is parse-verified against both). The converter and the integration tests accept either `qniverse` or the documented `Qniverse` casing, so no install step is needed there: upload or clone this repository, run `python demo.py`, then `python -m pytest tests/ -q` (install pytest in a cell with `!pip install pytest` if it is absent).

## Usage

```python
from qasm2qniverse import convert_qasm

source = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
"""

result = convert_qasm(source)          # version auto-detected; or version="2.0"
circuit = result.circuit               # QniverseCircuit
print(result.report.to_dict())         # status, warnings, unsupported, errors
print(circuit.qasm())                  # documented SDK export, for inspection
```

Lower-level split (no SDK needed for the first step):

```python
from qasm2qniverse import parse_qasm, build_circuit

ir, report = parse_qasm(source)        # works anywhere
circuit = build_circuit(ir)            # needs the Qniverse QSDK
```

## Inputs and outputs

- **Input**: OpenQASM 2.0/3.0 source as a string; optional explicit version.
- **Output**: `ConversionResult` with
  - `circuit`: the `QniverseCircuit` (qubit indices, register order, parameters, operation order and measurement mappings preserved),
  - `ir`: the intermediate representation,
  - `report`: `status` (`success` / `partial` / `failed`), `detected_version`, `mapped_operations`, register tables, and diagnostics with line numbers.
- **Errors**: fatal syntax problems raise `QasmSyntaxError`; the partial report is attached as `exc.report`. Sources containing unsupported statements raise `QasmConversionError` (report attached) by default - no executable circuit is returned for a partial conversion unless you pass `allow_partial=True`, which marks the report as a diagnostics-only build.

## Workflow and examples

`examples/` holds runnable samples: Bell (2.0), parameterized gates (2.0), multi-register (3.0), GHZ (3.0) and a file of unsupported constructs showing the diagnostics. Run them all:

```
python demo.py
```

Tests: `python -m pytest tests/ -q` (integration suite self-skips without the SDK).

## Qniverse/QSDK integration

The converter is deliberately a thin adapter over the documented SDK surface (`QniverseCircuit`, `QuantumRegister`, `ClassicalRegister`, `add_register`, `add_gate`, the `Qniverse.gates` catalog). Because the output is an ordinary `QniverseCircuit`, everything documented for circuits applies downstream: `qc.qasm()` export, `qc.draw(...)`, and remote execution on Qniverse backends with the account API key.

## Configuration and limitations

- No configuration files; the only option is the version override.
- Supported subset and the full unsupported list: `docs/04-supported-constructs.md`.
- Register names that violate QSDK naming rules are auto-renamed with a warning.
- The bundled reference simulator is for small-circuit equivalence checks only (exponential in qubits).
