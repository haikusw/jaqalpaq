"""Expand all macros in place in a ScheduledCircuit."""

from typing import Dict

from jaqalpaq import JaqalError
from jaqalpaq.core.visitor import Visitor
import jaqalpaq.core as core


def expand_macros(circuit):
    """Expand macros in the given circuit.

    :param circuit: The ScheduledCircuit to expand macros in.

    :returns: A new, normalized circuit. Although the circuit will be
    new, it may share structure with the input circuit, thus the input
    should not be changed.

    """

    visitor = MacroExpander()
    return visitor.visit(circuit)


class MacroExpander(Visitor):
    def visit_default(self, obj):
        """By default we leave all objects alone. Note that the object is not
        copied."""
        return obj

    def visit_ScheduledCircuit(self, circuit):
        """Return a new ScheduledCircuit with the same metadata and normalized
        gates."""

        self.macros = circuit.macros
        new_circuit = core.circuit.ScheduledCircuit(native_gates=circuit.native_gates)
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