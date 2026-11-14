OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
for int i in [0:2] { x q[0]; }
