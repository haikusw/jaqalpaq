"""Return all body statements that do not declare a macro."""

from .parse import TreeRewriteVisitor


def extract_body(tree):
    """Return all body statements (gates, loops, and code blocks) excluding macro definitions."""
    visitor = ExtractBodyVisitor()
    visitor.visit(tree)
    return visitor.statements


class ExtractBodyVisitor(TreeRewriteVisitor):

    def __init__(self):
        super().__init__()
        self.statements = None

    def visit_program(self, header_statements, body_statements):
        self.statements = body_statements
        return header_statements, body_statements

    def visit_macro_definition(self, name, arguments, block):
        return None
