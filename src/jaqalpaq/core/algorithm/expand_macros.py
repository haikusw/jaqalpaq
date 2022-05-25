# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Expand all macros in place in a Circuit."""

from typing import Dict

from jaqalpaq.error import JaqalError
from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.core.circuit import Circuit
from jaqalpaq.core.block import BlockStatement, LoopStatement
from jaqalpaq.core.gatedef import GateStatement
from jaqalpaq.core.macro import Macro
from jaqalpaq.core.register import Register, NamedQubit
from jaqalpaq.core.parameter import AnnotatedValue, Parameter


def expand_macros(circuit, preserve_definitions=False):
    """Expand macros in the given circuit.

    :param Circuit circuit: The circuit in which to expand macros.
    :param bool preserve_definitions: If True, leave the definitions in.

    :returns: A new, normalized circuit. Although the circuit will be
        new, it may share structure with the input circuit, thus the input
        should not be changed.
    :rtype: Circuit

    """

    visitor = MacroExpander(preserve_definitions=preserve_definitions)
    return visitor.visit(circuit)


class MacroExpander(Visitor):
    def __init__(self, preserve_definitions=False):
        self.preserve_definitions = preserve_definitions

    def visit_default(self, obj):
        """By default we leave all objects alone. Note that the object is not
        copied."""
        return obj

    def visit_Circuit(self, circuit):
        """Return a new Circuit with the same metadata and normalized
        gates."""

        self.macros = circuit.macros
        new_circuit = Circuit(native_gates=circuit.native_gates)
        if self.preserve_definitions:
            new_circuit.macros.update(circuit.macros)
        new_circuit.constants.update(circuit.constants)
        new_circuit.registers.update(circuit.registers)
        new_circuit.body.statements.extend(self.visit(circuit.body).statements)
        return new_circuit

    def visit_LoopStatement(self, loop):
        return LoopStatement(loop.iterations, self.visit(loop.statements))

    def visit_BlockStatement(self, block):
        new_statements = []
        for stmt in block.statements:
            new_stmt = self.visit(stmt)
            if (
                isinstance(new_stmt, BlockStatement)
                and new_stmt.parallel == block.parallel
            ):
                new_statements.extend(new_stmt.statements)
            else:
                new_statements.append(new_stmt)
        return BlockStatement(parallel=block.parallel, statements=new_statements)

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
    def __init__(self, arguments: Dict[str, AnnotatedValue], macros: Dict[str, Macro]):
        self.arguments = arguments
        self.macros = macros
        self.parameters = None

    def visit_default(self, obj):
        return obj

    def visit_Macro(self, macro: Macro):
        self.parameters = macro.parameters
        return self.visit(macro.body)

    def visit_BlockStatement(self, block: BlockStatement):
        return BlockStatement(
            parallel=block.parallel,
            statements=[self.visit(stmt) for stmt in block.statements],
        )

    def visit_LoopStatement(self, loop: LoopStatement):
        return LoopStatement(
            iterations=self.visit(loop.iterations),
            statements=self.visit(loop.statements),
        )

    def visit_GateStatement(self, gate: GateStatement):
        new_parameters = {
            name: self.visit(param) for name, param in gate.parameters.items()
        }
        new_gate = GateStatement(gate.gate_def, new_parameters)
        return replace_gate(new_gate, self.macros)

    def visit_Parameter(self, param: Parameter):
        if param.name in self.arguments:
            arg = self.arguments[param.name]
            # This check will basically always pass as Jaqal has no
            # way of type annotating macro arguments.
            param.validate(arg)
            return arg
        else:
            return param

    def visit_NamedQubit(self, qubit: NamedQubit):
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
