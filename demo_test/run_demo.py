"""Run every demo case through the C2-04 parser + reference simulator.

Usage (from anywhere):  python run_demo.py [path/to/C2-04]
Writes results.md and results.json next to this file.
Tolerance on probabilities: 1e-9.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
cands = ([sys.argv[1]] if len(sys.argv) > 1 else []) + [
    os.path.join(HERE, "C2-04"), os.path.join(HERE, "..", "C2-04"), "C2-04", "."]
REPO = next((os.path.abspath(p) for p in cands
             if os.path.isdir(os.path.join(p, "qasm2qniverse"))), None)
if REPO is None:
    sys.exit("C2-04 repo not found. Clone it: git clone https://github.com/Quantum-cdac/C2-04.git")
sys.path.insert(0, REPO)
import numpy as np
from qasm2qniverse import parse_qasm, QasmConversionError
from qasm2qniverse.simulator import simulate

TOL = 1e-9

def classical_dist(ir):
    """Distribution over classical bits as string c[n-1]...c[0]; qubit wire 0 = LSB."""
    probs = np.abs(simulate(ir)) ** 2
    qidx = {w: i for i, w in enumerate(ir.qubit_wires())}
    cidx = {(r.name, i): k for k, (r, i) in enumerate(
        (r, i) for r in ir.cregs for i in range(r.size))}
    meas = [(qidx[o.qargs[0]], cidx[o.cargs[0]]) for o in ir.operations if o.kind == "measure"]
    nc = ir.num_clbits
    out = {}
    for s, p in enumerate(probs):
        if p < 1e-15: continue
        bits = ["0"] * nc
        for q, c in meas:
            if (s >> q) & 1: bits[nc - 1 - c] = "1"
        k = "".join(bits)
        out[k] = out.get(k, 0.0) + float(p)
    return out

man = json.load(open(os.path.join(HERE, "manifest.json")))
rows, fails = [], 0
for cid, m in man.items():
    src = open(os.path.join(HERE, "cases", cid + ".qasm")).read()
    detail, ok = "", False
    try:
        ir, rep = parse_qasm(src)
        if m.get("reject"):
            ok = rep.status != "success"
            ents = [e for e in rep.entries if e.kind in ("unsupported", "error")]
            detail = f"status={rep.status}; " + "; ".join(f"line {e.line}: {e.message}" for e in ents[:2])
        else:
            got = classical_dist(ir)
            exp = m["dist"]
            ok = rep.status == "success" and set(got) == set(exp) and all(abs(got[k] - exp[k]) < TOL for k in exp)
            detail = "got " + json.dumps({k: round(v, 6) for k, v in got.items()})
    except QasmConversionError as e:
        ln = getattr(e, "line", None)
        if m.get("reject"):
            ok, detail = True, f"raised {type(e).__name__}: {e}"
        else:
            detail = f"UNEXPECTED {type(e).__name__}: {e}"
    except Exception as e:
        detail = f"CRASH {type(e).__name__}: {e}"
    fails += (not ok)
    rows.append({"case": cid, "category": m["category"], "result": "PASS" if ok else "FAIL", "detail": detail})
    print("PASS" if ok else "FAIL", "|", cid, "|", detail)

print(f"\n{len(rows)-fails}/{len(rows)} passed")
json.dump(rows, open(os.path.join(HERE, "results.json"), "w"), indent=1)
with open(os.path.join(HERE, "results.md"), "w") as f:
    f.write("| Case | Category | Result | Detail |\n|---|---|---|---|\n")
    for r in rows:
        f.write(f"| {r['case']} | {r['category']} | {r['result']} | {r['detail']} |\n")
sys.exit(1 if fails else 0)
