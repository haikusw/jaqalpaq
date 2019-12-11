from .parse import TreeRewriteVisitor

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
        return self._macro_args

    