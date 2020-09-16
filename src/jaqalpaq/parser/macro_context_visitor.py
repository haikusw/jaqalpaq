# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from .tree import TreeRewriteVisitor


class MacroContextRewriteVisitor(TreeRewriteVisitor):
    """A base class for visitors that need to account for whether they are operating in a macro context or not."""

    def __init__(self):
        self._macro_name = None
        self._macro_args = None

    @property
    def in_macro(self):
        """Return True if we are operating in a macro definition, False if we are at global scope."""
        return self.macro_name is not None

    @property
    def macro_name(self):
        """The name of the macro we are currently inside, or None if we are at global scope."""
        return self._macro_name

    @property
    def macro_args(self):
        """A list of Identifier objects which are the names of the arguments to the macro we are in. None if we
        are not in a macro."""
        return self._macro_args

    def visit_macro_header(self, name, arguments):
        self._macro_name = self.extract_identifier(name)
        self._macro_args = [self.extract_identifier(arg) for arg in arguments]

    def visit_macro_gate_block(self, block):
        # Since this method is called after visiting everything in the block, we clean up the context.
        self._macro_name = None
        self._macro_args = None
