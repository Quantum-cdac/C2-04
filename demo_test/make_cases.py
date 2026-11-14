import json, os
H2 = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n'
H3 = 'OPENQASM 3.0;\ninclude "stdgates.inc";\n'
M3 = 'measure q[0] -> c[0];\nmeasure q[1] -> c[1];\nmeasure q[2] -> c[2];\n'
R3 = H2 + 'qreg q[3];\ncreg c[3];\n'
H = 0.5
# (id, category, why, source, expect)  expect = {"dist": {...}} | {"reject": True}
C = [
("01_bell_qasm2","A-sanity","Basic Bell pair, QASM 2",H2+"qreg q[2];\ncreg c[2];\nh q[0];\ncx q[0], q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n",{"dist":{"00":H,"11":H}}),
("02_bell_qasm3","A-sanity","Same Bell pair, QASM 3 syntax",H3+"qubit[2] q;\nbit[2] c;\nh q[0];\ncx q[0], q[1];\nc = measure q;\n",{"dist":{"00":H,"11":H}}),
("03_ghz3","B-scope","3-qubit GHZ, QASM 3",H3+"qubit[3] q;\nbit[3] c;\nh q[0];\ncx q[0], q[1];\ncx q[1], q[2];\nc = measure q;\n",{"dist":{"000":H,"111":H}}),
("04_ccx_rz_demo","B-scope","Demo circuit: h, cx, ccx, rz",H3+"qubit[3] q;\nbit[3] c;\nh q[0];\ncx q[0], q[1];\nccx q[0], q[1], q[2];\nrz(pi/4) q[2];\nc = measure q;\n",{"dist":{"000":H,"111":H}}),
("05_multi_register","B-scope","Two registers map to global qubit order (a then b)",H2+"qreg a[1];\nqreg b[2];\ncreg c[3];\nx b[1];\nmeasure a[0] -> c[0];\nmeasure b[0] -> c[1];\nmeasure b[1] -> c[2];\n",{"dist":{"100":1.0}}),
("06_param_expressions","B-scope","pi expressions: rx(pi), ry(0.5*pi)*2 = full flip, u3(pi,0,pi)=X",H2+"qreg q[3];\ncreg c[3];\nrx(pi) q[0];\nry(pi/2) q[1];\nry(pi/2) q[1];\nu3(pi, 0, pi) q[2];\n"+M3,{"dist":{"111":1.0}}),
("07_barrier_ok","B-scope","Barrier is accepted and does not change the result",H2+"qreg q[2];\ncreg c[2];\nx q[1];\nbarrier q;\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n",{"dist":{"10":1.0}}),
("08_swap","B-scope","swap moves the excitation",H2+"qreg q[2];\ncreg c[2];\nx q[0];\nswap q[0], q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n",{"dist":{"10":1.0}}),
("09_if_unsupported","B-scope (fail loudly)","Classical conditional must be reported with its line",H3+"qubit[1] q;\nbit[1] c;\nif (c == 1) x q[0];\n",{"reject":True}),
("10_for_unsupported","B-scope (fail loudly)","Loop must be reported with its line",H3+"qubit[1] q;\nfor int i in [0:2] { x q[0]; }\n",{"reject":True}),
("11_gatedef_unsupported","B-scope (fail loudly)","User gate definition must be reported",H3+"qubit[1] q;\ngate mygate a { x a; }\n",{"reject":True}),
("12_sx_no_qsdk_gate","B-scope (fail loudly)","sx has no documented QSDK counterpart, must not be silently mapped",H3+"qubit[1] q;\nsx q[0];\n",{"reject":True}),
("13_bitorder_q0","C-boundary","x on q[0]: '001' means c[2]c[1]c[0] order",R3+"x q[0];\n"+M3,{"dist":{"001":1.0}}),
("14_max_index_q2","C-boundary","x on the highest index: '100'",R3+"x q[2];\n"+M3,{"dist":{"100":1.0}}),
("15_ccx_both_controls","C-boundary","Toffoli with both controls on flips the target",R3+"x q[0];\nx q[1];\nccx q[0], q[1], q[2];\n"+M3,{"dist":{"111":1.0}}),
("16_ccx_one_control","C-boundary","Toffoli with one control on does nothing",R3+"x q[0];\nccx q[0], q[1], q[2];\n"+M3,{"dist":{"001":1.0}}),
("17_angles_0_2pi_minus_pi","C-boundary","rz(0), rz(2*pi), rz(-pi) on |0> keep probabilities",H2+"qreg q[1];\ncreg c[1];\nrz(0) q[0];\nrz(2*pi) q[0];\nrz(-pi) q[0];\nmeasure q[0] -> c[0];\n",{"dist":{"0":1.0}}),
("18_measure_only","C-boundary","No gates at all: always 00",H2+"qreg q[2];\ncreg c[2];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n",{"dist":{"00":1.0}}),
("19_formatting_torture","C-boundary","Comments, blank lines, several statements per line",H2+"// comment\n\nqreg q[2]; creg c[2]; h q[0];cx q[0],q[1]; // tail\nmeasure q[0]->c[0];measure q[1]->c[1];\n",{"dist":{"00":H,"11":H}}),
("20_index_out_of_range","C-boundary (must reject)","q[3] on a 3-qubit register",H2+"qreg q[3];\ncreg c[3];\nx q[3];\n",{"reject":True}),
("21_undefined_gate","C-boundary (must reject)","Unknown gate name",H2+"qreg q[1];\nfoo q[0];\n",{"reject":True}),
("22_undeclared_register","C-boundary (must reject)","Register r never declared",H2+"qreg q[1];\nh r[0];\n",{"reject":True}),
("23_missing_semicolon","C-boundary (must reject)","Syntax error",H2+"qreg q[1];\nh q[0]\n",{"reject":True}),
("24_wrong_param_count","C-boundary (must reject)","rz needs 1 parameter",H2+"qreg q[1];\nrz q[0];\n",{"reject":True}),
("25_cx_same_qubit","C-boundary (must reject)","Control and target are the same qubit",H2+"qreg q[2];\ncx q[0], q[0];\n",{"reject":True}),
("26_divide_by_zero","C-boundary (must reject)","Constant expression divides by zero",H2+"qreg q[1];\nrz(1/0) q[0];\n",{"reject":True}),
("27_duplicate_register","C-boundary (must reject)","qreg declared twice",H2+"qreg q[2];\nqreg q[2];\n",{"reject":True}),
("28_missing_header","C-boundary (must reject)","No OPENQASM header","qreg q[1];\nh q[0];\n",{"reject":True}),
]
man = {}
for cid, cat, why, src, exp in C:
    open(f"cases/{cid}.qasm","w").write(src)
    man[cid] = {"category":cat,"why":why,**exp}
json.dump(man, open("manifest.json","w"), indent=1)
print(len(C), "cases written")
