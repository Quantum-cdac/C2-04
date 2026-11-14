"""Error types for the OpenQASM to QniverseCircuit converter."""


class QasmConversionError(Exception):
    """Base error for conversion failures."""


class QasmSyntaxError(QasmConversionError):
    """A statement could not be parsed.

    Attributes:
        line: 1-based line number in the source, if known.
        statement: the offending statement text (trimmed).
    """

    def __init__(self, message, line=None, statement=None):
        self.line = line
        self.statement = statement
        location = " at line %s" % line if line is not None else ""
        super().__init__("%s%s" % (message, location))
