"""Extract the constant mappings used by let statements."""
from .parse import TreeRewriteVisitor


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
        self.let_mapping[self.extract_identifier(identifier)] = number
