"""Export various symbols from a Jaqal file."""
from .parse import TreeRewriteVisitor
from .let_visitor import export_let_symbols

def export_symbols(tree):
    """Return all let statements and macro definitions in this file in a way that is suitable for inclusion in other
    Jaqal files."""

    lets = export_let_symbols(tree)

    transformer = ExportMacroTransformer()
    macros = transformer.visit(tree)
    return {'let': lets, 'macro': macros}


class ExportMacroTransformer(TreeRewriteVisitor):
    """A visitor that 0"""