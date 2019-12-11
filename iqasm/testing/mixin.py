from lark import Lark, Tree, Token

from iqasm.parse import make_lark_parser


class ParserTesterMixin:

    def make_parser(self, *args, **kwargs) -> Lark:
        return make_lark_parser(*args, **kwargs)

    @classmethod
    def simplify_tree(cls, tree):
        """Create a data structure with native Python types only retaining the information from the parse tree."""
        if isinstance(tree, Tree):
            return {'type': tree.data, 'children': [cls.simplify_tree(child) for child in tree.children]}
        elif isinstance(tree, Token):
            return {'type': tree.type, 'value': tree.value}
        else:
            raise TypeError(f'Unknown object in tree: {tree}')

    @staticmethod
    def make_program(header_statements, body_statements):
        return {'type': 'start', 'children': [header_statements, body_statements]}

    @staticmethod
    def make_register_statement(array_declaration):
        return {'type': 'register_statement', 'children': [array_declaration]}

    @classmethod
    def make_array_declaration(cls, name, length):
        return {'type': 'array_declaration', 'children': [cls.make_identifier(name), cls.make_integer(length)]}

    @classmethod
    def make_identifier(cls, name):
        return {'type': "IDENTIFIER", "value": str(name)}

    @classmethod
    def make_let_identifier(cls, name):
        return {'type': 'let_identifier', 'children': [cls.make_identifier(name)]}

    @classmethod
    def make_let_or_map_identifier(cls, name):
        return {'type': 'let_or_map_identifier', 'children': [cls.make_identifier(name)]}

    @classmethod
    def make_integer(cls, value):
        return {'type': 'INTEGER', 'value': str(value)}

    @classmethod
    def make_signed_integer(cls, value):
        return {'type': 'SIGNED_INTEGER', 'value': str(value)}

    @classmethod
    def make_signed_number(cls, value):
        return {'type': 'SIGNED_NUMBER', 'value': str(value)}

    @classmethod
    def make_map_statement(cls, target, source):
        return {'type': 'map_statement', 'children': [cls.make_identifier(target), source]}

    @classmethod
    def make_array_slice(cls, name, first_arg, *args):
        slices = [cls.make_integer(first_arg)]
        for arg in args:
            slices.append(cls.make_signed_integer(arg))
        return {'type': 'array_slice', 'children': [cls.make_identifier(name)] + slices}

    @classmethod
    def make_array_element(cls, name, index):
        return {'type': 'array_element', 'children': [cls.make_identifier(name), cls.make_integer(index)]}

    @classmethod
    def make_let_statement(cls, name, value):
        return {'type': 'let_statement', 'children': [cls.make_identifier(name), cls.make_signed_number(value)]}

    @classmethod
    def make_gate_statement(cls, name, *args):
        arg_children = [cls.make_gate_arg(arg) for arg in args]
        return {'type': 'gate_statement', 'children': [cls.make_identifier(name)] + arg_children}

    @classmethod
    def make_gate_arg(cls, arg):
        if isinstance(arg, str):
            return cls.make_let_or_map_identifier(arg)
        elif isinstance(arg, dict):
            # Already converted.
            return arg
        else:
            return cls.make_signed_number(arg)

    @classmethod
    def make_serial_gate_block(cls, *args):
        return {'type': 'sequential_gate_block', 'children': list(args)}

    @classmethod
    def make_parallel_gate_block(cls, *args):
        return {'type': 'parallel_gate_block', 'children': list(args)}

    @classmethod
    def make_macro_statement(cls, name, *args):
        gate_block = args[-1]
        args = args[:-1]
        children = [cls.make_identifier(name)] + [cls.make_identifier(arg) for arg in args] + [gate_block]
        return {'type': 'macro_definition', 'children': children}

    @classmethod
    def make_loop_statement(cls, iterations, block):
        if isinstance(iterations, int):
            iteration_var = cls.make_integer(iterations)
        else:
            iteration_var = cls.make_let_identifier(iterations)
        children = [iteration_var, block]
        return {'type': 'loop_statement', 'children': children}

    @classmethod
    def make_header_statements(cls, *statement_list):
        return {'type': 'header_statements', 'children': list(statement_list)}

    @classmethod
    def make_body_statements(cls, *statement_list):
        return {'type': 'body_statements', 'children': list(statement_list)}