# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Gather all macro definitions contained in a Jaqal file."""
from collections import namedtuple

from .tree import TreeRewriteVisitor
from jaqalpaq import JaqalError


def extract_macro(tree):
    """Return a dictionary mapping macro names to MacroRecord objects with their arguments and statements."""

    visitor = ExtractMacroVisitor()
    visitor.visit(tree)
    return visitor.macro_mapping


class ExtractMacroVisitor(TreeRewriteVisitor):
    def __init__(self):
        super().__init__()
        self.macro_mapping = {}

    def visit_macro_definition(self, name, arguments, block):
        name_id = self.extract_identifier(name)
        arg_ids = [self.extract_identifier(arg) for arg in arguments]
        if name_id in self.macro_mapping:
            raise JaqalError(f"Redefinition of {name_id} macro")
        self.macro_mapping[name_id] = MacroRecord(
            arg_ids, self.deconstruct_macro_gate_block(block)
        )
        return self.make_macro_definition(name, arguments, block)


MacroRecord = namedtuple("MacroRecord", ["arguments", "block"])
