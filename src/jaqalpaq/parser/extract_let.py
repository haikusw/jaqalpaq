# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Extract the constant mappings used by let statements."""
from .tree import TreeRewriteVisitor
from jaqalpaq import JaqalError


def extract_let(tree, use_float=False):
    """Return a dictionary mapping labels in let statements to parser tree fragments to be substituted.

    use_float -- If set to True, the resulting dictionary will map Identifier's to float's.

    Return a dictionary mapping Identifier's to parse tree fragments, unless use_float is True.
    """

    visitor = ExtractLetVisitor(use_float)
    visitor.visit(tree)
    return visitor.let_mapping


class ExtractLetVisitor(TreeRewriteVisitor):
    def __init__(self, use_float):
        super().__init__()
        self.use_float = bool(use_float)
        self.let_mapping = {}

    def visit_let_statement(self, identifier, number):
        if self.use_float:
            number = self.extract_signed_number(number)
        ext_identifier = self.extract_identifier(identifier)
        if ext_identifier in self.let_mapping:
            raise JaqalError(f"Redefinition of let-constant {ext_identifier}")
        self.let_mapping[ext_identifier] = number
