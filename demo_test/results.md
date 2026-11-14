| Case | Category | Result | Detail |
|---|---|---|---|
| 01_bell_qasm2 | A-sanity | PASS | got {"00": 0.5, "11": 0.5} |
| 02_bell_qasm3 | A-sanity | PASS | got {"00": 0.5, "11": 0.5} |
| 03_ghz3 | B-scope | PASS | got {"000": 0.5, "111": 0.5} |
| 04_ccx_rz_demo | B-scope | PASS | got {"000": 0.5, "111": 0.5} |
| 05_multi_register | B-scope | PASS | got {"100": 1.0} |
| 06_param_expressions | B-scope | PASS | got {"111": 1.0} |
| 07_barrier_ok | B-scope | PASS | got {"10": 1.0} |
| 08_swap | B-scope | PASS | got {"10": 1.0} |
| 09_if_unsupported | B-scope (fail loudly) | PASS | status=partial; line 5: dynamic/classical construct 'if' is outside the supported subset |
| 10_for_unsupported | B-scope (fail loudly) | PASS | status=partial; line 4: custom gate definitions and composite blocks are outside the supported subset |
| 11_gatedef_unsupported | B-scope (fail loudly) | PASS | status=partial; line 4: custom gate definitions and composite blocks are outside the supported subset |
| 12_sx_no_qsdk_gate | B-scope (fail loudly) | PASS | status=partial; line 4: gate 'sx' is not in the supported QSDK gate subset |
| 13_bitorder_q0 | C-boundary | PASS | got {"001": 1.0} |
| 14_max_index_q2 | C-boundary | PASS | got {"100": 1.0} |
| 15_ccx_both_controls | C-boundary | PASS | got {"111": 1.0} |
| 16_ccx_one_control | C-boundary | PASS | got {"001": 1.0} |
| 17_angles_0_2pi_minus_pi | C-boundary | PASS | got {"0": 1.0} |
| 18_measure_only | C-boundary | PASS | got {"00": 1.0} |
| 19_formatting_torture | C-boundary | PASS | got {"00": 0.5, "11": 0.5} |
| 20_index_out_of_range | C-boundary (must reject) | PASS | raised QasmSyntaxError: qubit index 3 out of range for register 'q' of size 3 at line 5 |
| 21_undefined_gate | C-boundary (must reject) | PASS | status=partial; line 4: gate 'foo' is not in the supported QSDK gate subset |
| 22_undeclared_register | C-boundary (must reject) | PASS | raised QasmSyntaxError: undeclared qubit register 'r' at line 4 |
| 23_missing_semicolon | C-boundary (must reject) | FAIL | status=success;  |
| 24_wrong_param_count | C-boundary (must reject) | PASS | raised QasmSyntaxError: gate 'rz' expects 1 parameter(s), got 0 at line 4 |
| 25_cx_same_qubit | C-boundary (must reject) | FAIL | status=success;  |
| 26_divide_by_zero | C-boundary (must reject) | FAIL | CRASH ZeroDivisionError: float division by zero |
| 27_duplicate_register | C-boundary (must reject) | PASS | raised QasmSyntaxError: duplicate register 'q' at line 4 |
| 28_missing_header | C-boundary (must reject) | PASS | raised QasmSyntaxError: missing OPENQASM version header at line 1 |
