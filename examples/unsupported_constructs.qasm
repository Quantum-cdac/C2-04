OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
bit c;
gate mygate a { x a; }
mygate q[0];
if (c == 1) x q[1];
for int i in [0:3] { h q[0]; }
c = measure q[0];
