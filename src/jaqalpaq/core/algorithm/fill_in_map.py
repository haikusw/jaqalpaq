# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Substitute a map alias directly into a circuit."""

from jaqalpaq.error import JaqalError
from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.core import circuitbuilder


def fill_in_map(circuit):
    """Substitute qubits from registers where aliases exist. Note this
    will fail if any macros use an alias as an argument.

    :param Circuit circuit: The circuit to fill in aliases.

    :returns: A new, normalized circuit. Although the circuit will be new, it may share
        structure with the input circuit, thus the input should not be changed.
    :rtype: Circuit

    The metadata will still contain all the map aliases but they will
    not be present in any gate.

    """

    visitor = MapFiller()
    return visitor.visit(circuit)


class MapFiller(Visitor):

    ##
    # Visitor Methods
    #

    def visit_default(self, obj):
        """Any object not covered in a rule can stay the same. This covers
        mostly scalar arguments to gates."""
        return obj

    def visit_Circuit(self, circuit):
        """Return a new circuit with all qubits resolved to indexed parts of
        registers."""
        body = self.visit(circuit.body)
        statements = body[1:]
        macros = [self.visit(macro) for macro in circuit.macros.values()]
        sexpr = [
            "circuit",
            *circuit.constants.values(),
            *circuit.registers.values(),
            *macros,
            *statements,
        ]
        inject_pulses = circuit.native_gates or None
        return circuitbuilder.build(sexpr, inject_pulses=inject_pulses)

    def visit_BlockStatement(self, block):
        if block.parallel:
            block_type = "parallel_block"
        else:
            block_type = "sequential_block"

        sexpr = [block_type, *(self.visit(stmt) for stmt in block.statements)]
        return sexpr

    def visit_LoopStatement(self, loop):
        sexpr = ["loop", self.visit(loop.iterations), self.visit(loop.statements)]
        return sexpr

    def visit_BranchStatement(self, branch):
        sexpr = ["branch", *(self.visit(case) for case in branch.cases)]
        return sexpr

    def visit_CaseStatement(self, case):
        sexpr = ["case", *(self.visit(stmt) for stmt in case.statements)]
        return sexpr

    def visit_GateStatement(self, gate):
        sexpr = [
            "gate",
            gate.name,
            *(self.visit(param) for param in gate.parameters.values()),
        ]
        return sexpr

    def visit_NamedQubit(self, qubit):
        """Map this to a fundamental register and index and return it."""
        reg, index = qubit.resolve_qubit()
        return reg[index]

    def visit_Register(self, reg):
        """If this is a fundamental register leave it be, otherwise let the
        user know that we can't properly fill in map aliases.

        This rule is reached when an argument to a gate is a full
        register, which is purposely not mentioned by the spec.

        """

        if reg.is_fundamental:
            return reg

        raise JaqalError(
            f"Cannot fill in map aliases: full alias {reg.name} found in statements"
        )

    def visit_Macro(self, macro):
        """Replace all map statements in a macro body just like anywhere
        else. The parameters internally have type Parameter, unlike single
        qubits which have type NamedQubit, so they are easily differentiated
        (unlike at the Jaqal level where they are both text identifiers).
        """
        gate_block = self.visit(macro.body)
        sexpr = [
            "macro",
            macro.name,
            *(param.name for param in macro.parameters),
            gate_block,
        ]
        return sexpr
