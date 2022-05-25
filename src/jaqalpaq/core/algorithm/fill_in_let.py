# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Fill in the value in a let-statement directly into a tree"""

from jaqalpaq.error import JaqalError
from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.core import circuitbuilder
from jaqalpaq.core.register import Register, NamedQubit
from jaqalpaq.core.constant import Constant


def fill_in_let(circuit, override_dict=None):
    """Fill in the value in a let-statement directly into the circuit.

    :param Circuit circuit: The circuit to fill in let statement constants.
    :param dict override_dict: A dictionary mapping strings to ints or floats to use
        instead of the values in the Jaqal file.

    :returns: A new, normalized circuit. Although the circuit will be new, it may share
        structure with the input circuit, thus the input should not be changed.
    :rtype: Circuit
    """

    visitor = LetFiller(override_dict)
    return visitor.visit(circuit)


class LetFiller(Visitor):
    def __init__(self, override_dict):
        super().__init__()
        self.override_dict = override_dict or {}

    ##
    # Visitor Methods
    #

    def visit_default(self, obj):
        """Any object not covered in a rule can stay the same. This covers
        mostly scalar arguments to gates."""
        return obj

    def visit_Circuit(self, circuit):
        """Return a new Circuit with all Constants replaced in the
        body. The new circuit will retain the same information in the
        circuit.constants attribute."""
        body = self.visit(circuit.body)
        statements = body[1:]
        reg_visitor = RegisterVisitor(self.override_dict)
        registers = [reg_visitor.visit(reg) for reg in circuit.registers.values()]
        macros = [self.visit(macro) for macro in circuit.macros.values()]
        sexpr = [
            "circuit",
            *circuit.constants.values(),
            *registers,
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

        sexpr = [block_type, *[self.visit(stmt) for stmt in block.statements]]
        return sexpr

    def visit_LoopStatement(self, loop):
        sexpr = ["loop", self.visit(loop.iterations), self.visit(loop.statements)]
        return sexpr

    def visit_CaseStatement(self, case):
        sexpr = ["case", self.visit(case.state), self.visit(case.statements)]
        return sexpr

    def visit_BranchStatement(self, branch):
        sexpr = ["branch", *[self.visit(case) for case in branch.cases]]
        return sexpr

    def visit_GateStatement(self, gate):
        sexpr = [
            "gate",
            gate.name,
            *[self.visit(param) for param in gate.parameters.values()],
        ]
        return sexpr

    def visit_Constant(self, const):
        return self.resolve_constant(const)

    def visit_NamedQubit(self, qubit):
        """Visit a named qubit that may possibly have its index
        remapped. Doing so will change the name of the qubit."""
        if isinstance(qubit.alias_index, Constant):
            new_index = self.resolve_constant(qubit.alias_index)
            new_from = self.visit(qubit.alias_from)
            return new_from[new_index]
        else:
            return qubit

    def visit_Register(self, reg):
        """Visit either a fundamental register or a map alias. Either may
        contain lurking let constants."""
        if reg.fundamental:
            if isinstance(reg.size, Constant):
                new_size = self.resolve_constant(reg.size)
                return ["register", reg.name, new_size]
            else:
                return reg
        else:
            new_alias_from = self.visit(reg.alias_from)
            if reg.alias_slice is None:
                new_alias_slice = None
            else:
                new_alias_slice = slice(
                    self.visit(reg.alias_slice.start),
                    self.visit(reg.alias_slice.stop),
                    self.visit(reg.alias_slice.step),
                )
            return Register(
                reg.name, alias_from=new_alias_from, alias_slice=new_alias_slice
            )

    def visit_Macro(self, macro):
        """Remove any references to let constants in this macro body while
        leaving alone any parameters that shadow those constants."""
        # Because let constants are of type Constant and parameters of
        # type Parameter, we don't have to do any extra work to track
        # this.
        gate_block = self.visit(macro.body)
        sexpr = [
            "macro",
            macro.name,
            *[param.name for param in macro.parameters],
            gate_block,
        ]
        return sexpr

    ##
    # Helper Methods
    #

    def resolve_constant(self, const):
        """Return the value for the given constant defined either in the
        override_dict or in the circuit itself."""
        if const.name in self.override_dict:
            return self.override_dict[const.name]
        if isinstance(const.value, (int, float)):
            return const.value
        else:
            # I don't think this can happen
            raise JaqalError(f"Constant {const.name} has non-numeric value")


class RegisterVisitor(LetFiller):
    """Specialization for handling registers and map aliases."""

    def __init__(self, override_dict):
        super().__init__(override_dict)

    def visit_NamedQubit(self, qubit):
        """Visit a named qubit that may possibly have its index
        remapped. Doing so will change the name of the qubit."""
        if isinstance(qubit.alias_index, Constant):
            new_index = self.resolve_constant(qubit.alias_index)
            new_from = self.visit(qubit.alias_from)
            return NamedQubit(qubit.name, new_from, new_index)
        else:
            return qubit
