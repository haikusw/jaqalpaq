# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Extract information on the usepulses statement used in a Jaqal file."""
# As we are specifically not using the full intended power of the usepulses statement,
# this module will be a very limited version. It will only support one such
# statement.

from .tree import TreeRewriteVisitor
from jaqalpaq import JaqalError


def extract_usepulses(tree):
    """Return a dictionary mapping usepulses objects to the objects extracted
    from them. If a value is None, that means the module is imported. If the value
    is all (yes, the built-in function), then all items are extracted into the
    local namespace.

    ex:

    usepulses foo
    from bar usepulses x, y, z
    from baz usepulses *

    yields

    {Identifier("foo"): None, Identifier("bar"): ["x", "y", "z"],
     Identifier("baz"): all}
    """

    visitor = ExtractUsepulsesVisitor()
    visitor.visit(tree)
    return visitor.usepulses_mapping


class ExtractUsepulsesVisitor(TreeRewriteVisitor):
    def __init__(self):
        self.usepulses_mapping = {}

    def visit_usepulses_statement(self, identifier, objects):
        ident_value = self.extract_qualified_identifier(identifier)
        if objects is not all:
            raise JaqalError("Only from foo usepulses * implemented")
        self.usepulses_mapping[ident_value] = objects
        return self.make_usepulses_statement(identifier, objects)
