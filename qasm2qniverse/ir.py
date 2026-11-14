"""Intermediate representation (IR) shared by the parser and the QSDK builder.

The parser produces an IR only; it never touches the Qniverse SDK. The builder
is the single module that translates the IR into a ``QniverseCircuit`` through
documented QSDK interfaces.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Register:
    """A quantum or classical register declaration.

    Attributes:
        name: register name as declared in the QASM source.
        size: number of wires.
        sdk_name: name safe for QSDK registration (alphabetic only), or None
            when the declared name is already valid.
    """

    name: str
    size: int
    sdk_name: Optional[str] = None

    @property
    def effective_sdk_name(self):
        return self.sdk_name if self.sdk_name else self.name


# A wire reference: (register name, index inside the register).
Wire = Tuple[str, int]


@dataclass
class Operation:
    """One circuit operation in source order.

    kind: "gate", "measure", "barrier" or "reset".
    name: gate name for kind == "gate" (already normalised to the QSDK name).
    params: evaluated float parameters, in source order.
    qargs: target qubit wires, in source order. For a measure operation this
        holds the single measured qubit.
    cargs: for a measure operation, the single classical target wire.
    line: 1-based source line, for diagnostics.
    """

    kind: str
    name: Optional[str] = None
    params: List[float] = field(default_factory=list)
    qargs: List[Wire] = field(default_factory=list)
    cargs: List[Wire] = field(default_factory=list)
    line: Optional[int] = None


@dataclass
class CircuitIR:
    """Parsed program: registers plus the ordered operation list."""

    version: str
    qregs: List[Register] = field(default_factory=list)
    cregs: List[Register] = field(default_factory=list)
    operations: List[Operation] = field(default_factory=list)

    @property
    def num_qubits(self):
        return sum(r.size for r in self.qregs)

    @property
    def num_clbits(self):
        return sum(r.size for r in self.cregs)

    def qubit_wires(self):
        """All qubit wires in global order (declaration order, index ascending)."""
        return [(r.name, i) for r in self.qregs for i in range(r.size)]
