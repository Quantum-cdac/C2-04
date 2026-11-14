OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
bit[1] c;
if (c == 1) x q[0];
