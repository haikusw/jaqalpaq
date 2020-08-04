# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Expand all macros in place in a Circuit."""

from typing import Dict

from jaqalpaq import JaqalError
from jaqalpaq.core.algorithm.visitor import Visitor
import jaqalpaq.core as core


def expand_macros(circuit):
    """Expand macros in the given circuit.

    :param Circuit circuit: The circuit in which to expand macros.

    :returns: A new, normalized circuit. Although the circuit will be
        new, it may share structure with the input circuit, thus the input
        should not be changed.
    :rtype: Circuit

    """

    visitor = MacroExpander()
    return visitor.visit(circuit)


class MacroExpander(Visitor):
    def visit_default(self, obj):
        """By default we leave all objects alone. Note that the object is not
        copied."""
        return obj

    def visit_Circuit(self, circuit):
        """Return a new Circuit with the same metadata and normalized
        gates."""

        self.macros = circuit.macros
        new_circuit = core.circuit.Circuit(native_gates=circuit.native_gates)
        new_circuit.constants.update(circuit.constants)
        new_circuit.registers.update(circuit.registers)
        new_circuit.body.statements.extend(self.visit(circuit.body).statements)
        return new_circuit

    def visit_LoopStatement(self, loop):
        return core.LoopStatement(loop.iterations, self.visit(loop.statements))

    def visit_BlockStatement(self, block):
        new_statements = []
        for stmt in block.statements:
            new_stmt = self.visit(stmt)
            if (
                isinstance(new_stmt, core.BlockStatement)
                and new_stmt.parallel == block.parallel
            ):
                new_statements.extend(new_stmt.statements)
            else:
                new_statements.append(new_stmt)
        return core.BlockStatement(parallel=block.parallel, statements=new_statements)

    def visit_GateStatement(self, gate):
        return replace_gate(gate, self.macros)


def replace_gate(gate, macros):
    """Replace a gate with its definition in macros, or return the gate if
    it is not a macro."""
    if gate.name in macros:
        macro = macros[gate.name]
        if len(gate.parameters) != len(macro.parameters):
            raise JaqalError(
                f"Cannot expand {gate.name}: wrong argument count: {len(gate.parameters)} != {len(macro.parameters)}"
            )
        visitor = GateReplacer(gate.parameters, macros)
        return visitor.visit(macro)
    else:
        return gate


class GateReplacer(Visitor):
    def __init__(
        self, arguments: Dict[str, core.AnnotatedValue], macros: Dict[str, core.Macro]
    ):
        self.arguments = arguments
        self.macros = macros
        self.parameters = None

    def visit_default(self, obj):
        return obj

    def visit_Macro(self, macro: core.Macro):
        self.parameters = macro.parameters
        return self.visit(macro.body)

    def visit_BlockStatement(self, block: core.BlockStatement):
        return core.BlockStatement(
            parallel=block.parallel,
            statements=[self.visit(stmt) for stmt in block.statements],
        )

    def visit_LoopStatement(self, loop: core.LoopStatement):
        return core.LoopStatement(
            iterations=self.visit(loop.iterations),
            statements=self.visit(loop.statements),
        )

    def visit_GateStatement(self, gate: core.GateStatement):
        new_parameters = {
            name: self.visit(param) for name, param in gate.parameters.items()
        }
        new_gate = core.GateStatement(gate.gate_def, new_parameters)
        return replace_gate(new_gate, self.macros)

    def visit_Parameter(self, param: core.Parameter):
        if param.name in self.arguments:
            arg = self.arguments[param.name]
            # This check will basically always pass as Jaqal has no
            # way of type annotating macro arguments.
            param.validate(arg)
            return arg
        else:
            return param

    def visit_NamedQubit(self, qubit: core.NamedQubit):
        """This happens when the user indexes a qubit register."""
        alias_from = self.visit(qubit.alias_from)
        alias_index = filter_float(self.visit(qubit.alias_index))
        return alias_from[alias_index]


def filter_float(value):
    """Change a floating point value that represents an integer into an
    integer."""
    if isinstance(value, float) and float(value) == int(value):
        return int(value)
    return value
