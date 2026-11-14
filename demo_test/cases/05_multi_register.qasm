OPENQASM 2.0;
include "qelib1.inc";
qreg a[1];
qreg b[2];
creg c[3];
x b[1];
measure a[0] -> c[0];
measure b[0] -> c[1];
measure b[1] -> c[2];
