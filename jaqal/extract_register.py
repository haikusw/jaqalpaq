"""Extract information on the regisers used in a Jaqal file."""
from .parse import TreeRewriteVisitor


def extract_register(tree):
    """Return a dictionary mapping register names to their size. An exception will be raised if a register is
    declared twice, as this would not show up in the output. However this function allows for multiple register
    statements to be present."""

    visitor = ExtractRegisterVisitor()
    visitor.visit(tree)
    return visitor.register_mapping


class ExtractRegisterVisitor(TreeRewriteVisitor):

    def __init__(self):
        super().__init__()
        self.register_mapping = {}

    def visit_register_statement(self, array_declaration):
        identifier, size = self.deconstruct_array_declaration(array_declaration)
        if str(identifier) in self.register_mapping:
            raise ValueError(f'Redefinition of register {identifier}')
        self.register_mapping[str(identifier)] = int(size)
