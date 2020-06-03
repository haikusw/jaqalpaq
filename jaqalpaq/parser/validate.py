"""Validate a parse tree to catch errors that aren't pure syntax errors but still exist at the language level."""

from numbers import Integral

from .tree import TreeRewriteVisitor


def validate(tree, registers):
    """Perform validations on this parse tree after all resolution has occurred."""
    validate_registers(tree, registers)
    for name, size in registers.items():
        if not isinstance(size, Integral):
            raise ValueError(f"Register {name} has bad size {size}")


def validate_registers(tree, registers):
    """Validate that every gate argument that isn't a number refers to a register in the registers argument. This
    validator is expected to be called after all resolutions in the tree. Also check that each index is between
    zero and the maximum value for the register."""

    visitor = ValidateRegistersVisitor(registers)
    visitor.visit(tree)


class ValidateRegistersVisitor(TreeRewriteVisitor):
    def __init__(self, registers):
        super().__init__()
        self.registers = registers

    def visit_let_or_map_identifier(self, identifier):
        name = str(self.extract_qualified_identifier(identifier))
        if name not in self.registers:
            raise ValueError(f"Unresolved register {name}")
        return self.make_let_or_map_identifier(identifier)

    def visit_let_identifier(self, identifier):
        name = str(self.extract_qualified_identifier(identifier))
        if name not in self.registers:
            raise ValueError(f"Unresolved register {name}")
        return self.make_let_identifier(identifier)

    def visit_array_element_qual(self, identifier, index):
        name = str(self.extract_qualified_identifier(identifier))
        if name not in self.registers:
            raise ValueError(f"Unresolved register {name}")
        index_value = self.extract_signed_integer(index)
        if not (0 <= index_value < self.registers[name]):
            raise ValueError(f"Invalid index {index_value} for register {name}")
        return self.make_let_identifier(identifier)