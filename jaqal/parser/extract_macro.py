"""Gather all macro definitions contained in a Jaqal file."""
from collections import namedtuple

from .parse import TreeRewriteVisitor


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
            raise ValueError(f"Redefinition of {name_id} macro")
        self.macro_mapping[name_id] = MacroRecord(arg_ids, self.deconstruct_macro_gate_block(block))
        return self.make_macro_definition(name, arguments, block)


MacroRecord = namedtuple('MacroRecord', ['arguments', 'block'])