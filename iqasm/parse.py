"""Parsing related functions and data types"""

from abc import ABC, abstractmethod
import pathlib

from lark import Lark, Transformer, Tree, Token


def parse_with_lark(text_or_fd, *args, **kwargs):
    """Parse the given text or file descriptor using Lark. Return the Lark parse tree."""
    parser = make_lark_parser(*args, **kwargs)
    tree = parser.parse(text_or_fd)
    return tree


def make_lark_parser(*args, **kwargs):
    """Create a lark parser with some default arguments."""
    kwargs_with_defaults = {
        'start': 'start',
        'parser': 'lalr',
        **kwargs
    }
    with open(get_grammar_path(), 'r') as fd:
        parser = Lark(fd, *args, **kwargs_with_defaults)
    return parser


def get_grammar_path(filename='iqasm_grammar.lark'):
    """Return the path to the lark grammar file."""
    return pathlib.Path(__file__).parent / filename


class VisitTransformer(Transformer):
    """A Lark transformer that traverses the tree and calls the appropriate methods in the ParseTreeVisitor class.

    If you're unsure of whether you should be using this class, you should not be using this class.
    """

    def __init__(self, visitor):
        super().__init__(visit_tokens=True)
        self._visitor = visitor

    def start(self, args):
        header_statements, body_statements = args
        return self._visitor.visit_program(header_statements, body_statements)

    def register_statement(self, args):
        array_declaration, = args
        return self._visitor.visit_register_statement(array_declaration)

    def map_statement(self, args):
        target, source = args
        return self._visitor.visit_map_statement(target, source)

    def let_statement(self, args):
        identifier, number = args
        return self._visitor.visit_let_statement(identifier, number)

    def body_statements(self, args):
        return args

    def header_statements(self, args):
        return args

    def gate_statement(self, args):
        gate_name = args[0]
        gate_args = args[1:]
        return self._visitor.visit_gate_statement(gate_name, gate_args)

    def macro_definition(self, args):
        identifiers = args[:-1]
        gate_block = args[-1]
        macro_name = identifiers[0]
        macro_args = identifiers[1:]
        return self._visitor.visit_macro_definition(macro_name, macro_args, gate_block)

    def loop_statement(self, args):
        repetition_count, block = args
        return self._visitor.visit_loop_statement(repetition_count, block)

    def sequential_gate_block(self, args):
        return self._visitor.visit_sequential_gate_block(args)

    def parallel_gate_block(self, args):
        return self._visitor.visit_parallel_gate_block(args)

    def array_declaration(self, args):
        identifier, size = args
        return self._visitor.visit_array_declaration(identifier, size)

    def array_element(self, args):
        identifier, index = args
        return self._visitor.visit_array_element(identifier, index)

    def array_slice(self, args):
        identifier = args[0]
        slice_args = args[1:]
        index_slice = slice(*slice_args)
        return self._visitor.visit_array_slice(identifier, index_slice)

    def IDENTIFIER(self, string):
        return self._visitor.visit_identifier(string)

    def SIGNED_NUMBER(self, string):
        return self._visitor.visit_signed_number(string)

    def NUMBER(self, string):
        return self._visitor.visit_number(string)

    def INTEGER(self, string):
        return self._visitor.visit_integer(string)

    def SIGNED_INTEGER(self, string):
        return self._visitor.visit_signed_integer(string)


class ParseTreeVisitor(ABC):
    """A visitor used to traverse a parse tree. Although it works directly on parse trees used by the underlying
    parser library, the user is not exposed to this detail.

    Methods in this visitor are designed to be overridden. Those without default implementations (mostly token-level
    methods) must be overridden to implement the visitor. The parse tree is visited from the bottom up. Therefore
    each method gets the results of lower visitations as its arguments, except for tokens, which get the raw string if
    they are overridden.

    """

    # Derived classes may overwrite this to change behavior.
    transformer_class = VisitTransformer

    def visit(self, tree):
        """Visit this tree and return the result of successively calling the visit_* methods."""
        transformer = VisitTransformer(self)
        return transformer.transform(tree)

    ##
    # Token-level methods
    #

    def visit_identifier(self, identifier_string):
        return str(identifier_string)

    def visit_signed_number(self, string):
        if '.' in string or 'e' in string or 'E' in string:
            return float(string)
        else:
            return int(string)

    def visit_number(self, string):
        if '.' in string or 'e' in string or 'E' in string:
            return float(string)
        else:
            return int(string)

    def visit_integer(self, string):
        return int(string)

    def visit_signed_integer(self, string):
        return int(string)

    ##
    # Mandatory overrides
    #

    @abstractmethod
    def visit_program(self, header_statements, body_statements):
        """Visit the 'start' rule in the grammar. Header statements and body statements are automatically gathered
        into a list after calling the appropriate header or body statement on each."""
        pass

    @abstractmethod
    def visit_register_statement(self, array_declaration):
        pass

    @abstractmethod
    def visit_map_statement(self, target, source):
        pass

    @abstractmethod
    def visit_let_statement(self, identifier, number):
        pass

    @abstractmethod
    def visit_gate_statement(self, gate_name, gate_args):
        """Visit a gate. The args are gathered into a list or identifiers, numbers, and array elements."""
        pass

    @abstractmethod
    def visit_macro_definition(self, name, arguments, block):
        """Visit a macro definition. The arguments are gathered into a list, but the block is merely the result of
        the appropriate visit_*_block method."""
        pass

    @abstractmethod
    def visit_loop_statement(self, repetition_count, block):
        """Visit a loop statement. The repetition count is either an integer or identifier."""
        pass

    @abstractmethod
    def visit_sequential_gate_block(self, statements):
        """Visit a gate block of sequential statements. Each statement is a gate statement, macro definition, or
        loop statement. Therefore it is important to be able to differentiate between the results of the appropriate
        visit_* methods."""
        pass

    @abstractmethod
    def visit_parallel_gate_block(self, statements):
        """Same as visit_sequential_gate_block, but intended for parallel execution."""
        pass

    @abstractmethod
    def visit_array_declaration(self, identifier, size):
        """Visit an array declaration, currently used in map and register statements. The identifier is the label
        the user wishes to use, and the size is either an identifier or integer."""
        pass

    @abstractmethod
    def visit_array_element(self, identifier, index):
        """Visit an array, dereferenced to a single element. The index is either an identifier or integer."""
        pass

    @abstractmethod
    def visit_array_slice(self, identifier, index_slice):
        """Visit an array dereferenced by slice, as used in the map statement. The identifier is the name of the
        existing array, and index_slice is a Python slice object. None represents the lack of a bound, an integer a
        definite bound, and a string is an identifier used as that bound."""
        pass


class TreeRewriteVisitor(ParseTreeVisitor):
    """A base class that serves to mostly rewrite a parse tree without knowing the exact implementation of the tree.
    Each method by default returns or reconstructs its portion of the tree."""

    ##
    # Overrides of visit methods
    #

    def visit_identifier(self, token):
        return token

    def visit_signed_number(self, token):
        return token

    def visit_number(self, token):
        return token

    def visit_integer(self, token):
        return token

    def visit_signed_integer(self, token):
        return token

    def visit_program(self, header_statements, body_statements):
        return self.make_program(header_statements, body_statements)

    def visit_register_statement(self, array_declaration):
        return self.make_register_statement(array_declaration)

    def visit_map_statement(self, target, source):
        return self.make_map_statement(target, source)

    def visit_let_statement(self, identifier, number):
        return self.make_let_statement(identifier, number)

    def visit_gate_statement(self, gate_name, gate_args):
        return self.make_gate_statement(gate_name, gate_args)

    def visit_macro_definition(self, name, arguments, block):
        return self.make_macro_definition(name, arguments, block)

    def visit_loop_statement(self, repetition_count, block):
        return self.make_loop_statement(repetition_count, block)

    def visit_sequential_gate_block(self, statements):
        return self.make_sequential_gate_block(statements)

    def visit_parallel_gate_block(self, statements):
        return self.make_parallel_gate_block(statements)

    def visit_array_declaration(self, identifier, size):
        return self.make_array_declaration(identifier, size)

    def visit_array_element(self, identifier, index):
        return self.make_array_element(identifier, index)

    def visit_array_slice(self, identifier, index_slice):
        return self.make_array_slice(identifier, index_slice)

    ##
    # New methods to construct parts of the tree
    #

    def make_program(self, header_statements, body_statements):
        return Tree('start', [Tree('header_statements', header_statements), Tree('body_statements', body_statements)])

    def make_register_statement(self, array_declaration):
        return Tree('register_statement', [array_declaration])

    def make_map_statement(self, target, source):
        return Tree('map_statement', [target, source])

    def make_let_statement(self, identifier, number):
        return Tree('let_statement', [identifier, number])

    def make_gate_statement(self, gate_name, gate_args):
        return Tree('gate_statement', [gate_name] + gate_args)

    def make_macro_definition(self, name, arguments, block):
        return Tree('macro_definition', [name] + arguments + [block])

    def make_loop_statement(self, repetition_count, block):
        return Tree('loop_statement', [repetition_count, block])

    def make_sequential_gate_block(self, statements):
        return Tree('sequential_gate_block', statements)

    def make_parallel_gate_block(self, statements):
        return Tree('parallel_gate_block', statements)

    def make_array_declaration(self, identifier, size):
        return Tree('array_declaration', [identifier, size])

    def make_array_element(self, identifier, index):
        return Tree('array_element', [identifier, index])

    def make_array_slice(self, identifier, index_slice):
        # TODO: This is not quite right, but we should revisit this when correcting array slice semantics.
        return Tree('array_slice', [identifier] + [index for index in [index_slice.start, index_slice.stop, index_slice.step]
                                                   if index is not None])

    def make_identifier(self, identifier_string):
        return Token('IDENTIFIER', identifier_string)

    def make_signed_number(self, number):
        if not isinstance(number, float) and not isinstance(number, int):
            raise TypeError(f"Expected number, found {number}")
        return Token('SIGNED_NUMBER', str(number))

    def make_number(self, number):
        if (not isinstance(number, float) and not isinstance(number, int)) or number < 0:
            raise TypeError(f"Expected non-negative number, found {number}")
        return Token('NUMBER', str(number))

    def make_integer(self, number):
        if not isinstance(number, int) or number < 0:
            raise TypeError(f"Expected non-negative integer, found {number}")
        return Token('INTEGER', str(number))

    def make_signed_integer(self, number):
        if not isinstance(number, int):
            raise TypeError(f"Expected integer, found {number}")
        return Token('SIGNED_INTEGER', str(number))
