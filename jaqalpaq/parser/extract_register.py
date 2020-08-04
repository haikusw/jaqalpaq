# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Extract information on the registers used in a Jaqal file."""
from .tree import TreeRewriteVisitor
from .identifier import Identifier
from jaqalpaq import JaqalError


def extract_register(tree):
    """Return a dictionary mapping register names to their size. An exception will be raised if a register is
    declared twice, as this would not show up in the output. However this function allows for multiple register
    statements to be present. The size is expressed as a parse tree because it is legal to refer to a value defined
    in a let statement."""

    visitor = ExtractRegisterVisitor()
    visitor.visit(tree)
    return visitor.register_mapping


class ExtractRegisterVisitor(TreeRewriteVisitor):
    def __init__(self):
        super().__init__()
        self.register_mapping = {}

    def visit_register_statement(self, array_declaration):
        identifier, size = self.deconstruct_array_declaration(array_declaration)
        identifier = Identifier.parse(identifier)
        if identifier in self.register_mapping:
            raise JaqalError(f"Redefinition of register {identifier}")
        self.register_mapping[identifier] = self.make_let_or_integer(size)
