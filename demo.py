"""Demo: convert every example QASM file and print its conversion report.

Works without the Qniverse SDK (parsing, validation and reporting are
SDK-independent); when the SDK is installed it also builds the
QniverseCircuit and prints the circuit's documented QASM export.

Usage: python demo.py [examples-dir]
"""

import json
import os
import sys

from qasm2qniverse import (
    QasmConversionError,
    QasmSyntaxError,
    build_circuit,
    convert_qasm,
    parse_qasm,
)


def run(path):
    with open(path) as handle:
        source = handle.read()
    print("=" * 72)
    print(os.path.basename(path))
    try:
        ir, report = parse_qasm(source)
    except QasmSyntaxError as exc:
        print("FATAL:", exc)
        print(json.dumps(exc.report.to_dict(), indent=2))
        return
    print(json.dumps(report.to_dict(), indent=2))
    if report.status != "success":
        print(
            "[strict mode: convert_qasm would raise here; pass "
            "allow_partial=True for a diagnostics-only build]"
        )
        try:
            convert_qasm(source)
        except QasmConversionError as exc:
            print("convert_qasm raised as designed:", exc)
        return
    try:
        circuit = build_circuit(ir)
    except ImportError:
        print("[Qniverse QSDK not installed here; circuit build skipped]")
        return
    print("--- QniverseCircuit.qasm() (documented SDK export) ---")
    print(circuit.qasm())


def main():
    examples = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "examples"
    )
    for name in sorted(os.listdir(examples)):
        if name.endswith(".qasm"):
            run(os.path.join(examples, name))


if __name__ == "__main__":
    main()
