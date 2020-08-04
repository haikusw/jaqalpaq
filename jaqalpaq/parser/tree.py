# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Functions and data types creating and acting on parse trees."""

from abc import ABC, abstractmethod
from functools import wraps, lru_cache
import pathlib

from lark import Lark, Transformer, Tree, Token
from lark.exceptions import UnexpectedInput

from .identifier import Identifier
from jaqalpaq import JaqalError


def parse_with_lark(text, *args, **kwargs):
    """Parse the given text using Lark. Return the Lark parse tree."""
    parser = make_lark_parser(*args, **kwargs)
    try:
        return parser.parse(text)
    except UnexpectedInput as exc:
        raise JaqalParseError(
            f"Expected: {list(exc.expected)}, found: `{exc.token}`",
            line=exc.line,
            column=exc.column,
        )


@lru_cache(maxsize=16)
def make_lark_parser(*args, **kwargs):
    """Create a lark parser with some default arguments."""
    kwargs_with_defaults = {"start": "start", "parser": "lalr", **kwargs}
    with open(get_grammar_path(), "r") as fd:
        parser = PreprocessingLarkParser(fd, *args, **kwargs_with_defaults)
    return parser


class PreprocessingLarkParser(Lark):
    """Subclass of lark parsers that run preparsing steps. As this may be
    cached it should be considered immutable once created."""

    def parse(self, *args, **kwargs):
        tree = super().parse(*args, **kwargs)
        tree = expand_qualified_identifiers(tree)
        return tree


def get_grammar_path(filename="jaqal_grammar.lark"):
    """Return the path to the lark grammar file."""
    return pathlib.Path(__file__).parent / filename


def expand_qualified_identifiers(tree):
    """Expand qualified identifier tokens into trees. This step is a hack to disallow spaces between elements of a
    qualified identifier but still allow downstream elements to see them broken out by element."""

    transformer = QualifiedIdentifierTransformer(visit_tokens=True)
    return transformer.transform(tree)


class LarkTransformerBase(Transformer):
    """Base for transformers based on the Lark Transformer class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The last token read. This is used to get an approximation of
        # the position of errors. We start with an invalid, zero-size
        # token at the beginnning to avoid dereferencing an invalid
        # object before the first token is read.
        self.last_token = Token(
            "INVALID",
            "",
            pos_in_stream=0,
            line=0,
            column=0,
            end_line=0,
            end_column=0,
            end_pos=0,
        )

    ##
    # Position properties
    #
    # Note: These are approximate as they pick the last token
    # processed inside an expression and use that as its
    # position. This should be good enough for debugging purposes
    #

    @property
    def current_line(self):
        """Return a line associated with the current item being processed."""
        return self.last_token.line

    @property
    def current_column(self):
        """Return a column associated with the current item being
        processed."""
        return self.last_token.column

    @property
    def current_pos(self):
        """Return a position in the input character stream associated with the
        current item being processed."""
        return self.last_token.pos_in_stream


def token_method(method):
    """Decorator used in classes derived from LarkTransformerBase to
    indicate they are handling a token."""

    @wraps(method)
    def wrapped_method(self, token):
        self.last_token = token
        return method(self, token)

    return wrapped_method


class QualifiedIdentifierTransformer(LarkTransformerBase):
    """Transformer class to replace instances of QUALIFIED_IDENTIFIER tokens with qualified_identifier trees."""

    @token_method
    def QUALIFIED_IDENTIFIER(self, string):
        parts = Identifier.parse(string)
        children = []

        # Assign positions in the original text to portions of the
        # token. This doesn't have to be perfect as it's only useful
        # in error messages.
        remaining_token = str(string)
        for part in parts:
            offset = remaining_token.find(part)
            remaining_token = remaining_token[offset + len(part) :]
            # Assume a token cannot cross lines, which I think is true
            # for Jaqal
            token = Token(
                "IDENTIFIER",
                part,
                pos_in_stream=string.pos_in_stream + offset,
                line=string.line,
                column=string.column + offset,
                end_line=string.end_line,
                end_column=string.column + offset + len(part),
                end_pos=string.pos_in_stream + offset + len(part),
            )
            children.append(token)

        return Tree("qualified_identifier", children=children)


class VisitTransformer(LarkTransformerBase):
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
        (array_declaration,) = args
        return self._visitor.visit_register_statement(array_declaration)

    def map_statement(self, args):
        target, source = args
        return self._visitor.visit_map_statement(target, source)

    def let_statement(self, args):
        identifier, number = args
        return self._visitor.visit_let_statement(identifier, number)

    def usepulses_statement(self, args):
        if len(args) != 2:
            raise JaqalError("Only from foo usepulses * implemented")
        if args[0].data == "from_clause":
            if args[1].data != "all_module":
                raise JaqalError("Only from foo usepulses * implemented")
            identifier = args[0].children[0]
            objects = all
        else:
            raise JaqalError("Only from foo usepulses * implemented")
        return self._visitor.visit_usepulses_statement(identifier, objects)

    def body_statements(self, args):
        return [stmt for stmt in args if stmt is not None]

    def header_statements(self, args):
        return [stmt for stmt in args if stmt is not None]

    def gate_statement(self, args):
        gate_name = args[0]
        gate_args = args[1:]
        return self._visitor.visit_gate_statement(gate_name, gate_args)

    def macro_definition(self, args):
        identifiers = args[0].children
        gate_block = args[1]
        macro_name = identifiers[0]
        macro_args = identifiers[1:]
        return self._visitor.visit_macro_definition(macro_name, macro_args, gate_block)

    def macro_header(self, args):
        macro_name = args[0]
        macro_args = args[1:]
        ret = self._visitor.visit_macro_header(macro_name, macro_args)
        if ret is None:
            # This allows macro_header to be optional in the visitor
            return Tree("macro_header", args)
        else:
            return ret

    def macro_gate_block(self, args):
        block = args[0]
        ret = self._visitor.visit_macro_gate_block(block)
        if ret is None:
            # This allows macro_block to be optional in the visitor
            return Tree("macro_gate_block", args)
        else:
            return ret

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

    def array_element_qual(self, args):
        identifier, index = args
        return self._visitor.visit_array_element_qual(identifier, index)

    def array_slice(self, args):
        identifier = args[0]
        slice_args = args[1:]
        index_slice = slice(*slice_args)
        return self._visitor.visit_array_slice(identifier, index_slice)

    def array_slice_start(self, args):
        return self._array_slice_element(args)

    def array_slice_stop(self, args):
        return self._array_slice_element(args)

    def array_slice_step(self, args):
        return self._array_slice_element(args)

    def _array_slice_element(self, args):
        if args:
            return args[0]
        else:
            return None

    def let_identifier(self, args):
        identifier = args[0]
        return self._visitor.visit_let_identifier(identifier)

    def let_or_map_identifier(self, args):
        identifier = args[0]
        return self._visitor.visit_let_or_map_identifier(identifier)

    def qualified_identifier(self, args):
        names = tuple(name for name in args)
        return self._visitor.visit_qualified_identifier(names)

    @token_method
    def IDENTIFIER(self, string):
        return self._visitor.visit_identifier(string)

    @token_method
    def SIGNED_NUMBER(self, string):
        return self._visitor.visit_signed_number(string)

    @token_method
    def NUMBER(self, string):
        return self._visitor.visit_number(string)

    @token_method
    def INTEGER(self, string):
        return self._visitor.visit_integer(string)

    @token_method
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

    def visit(self, tree):
        """Visit this tree and return the result of successively calling the visit_* methods."""
        self.transformer = VisitTransformer(self)
        try:
            return self.transformer.transform(tree)
        except Exception as exc:
            raise JaqalParseError(
                str(exc), self.transformer.current_line, self.transformer.current_column
            )

    @property
    def current_line(self):
        """Return a line associated with the current item being processed."""
        if not hasattr(self, "transformer"):
            raise JaqalError("Cannot call current_line before visit")
        return self.transformer.current_line

    @property
    def current_column(self):
        """Return a column associated with the current item being
        processed."""
        if not hasattr(self, "transformer"):
            raise JaqalError("Cannot call current_column before visit")
        return self.transformer.current_column

    @property
    def current_pos(self):
        """Return a position in the input character stream associated with the
        current item being processed."""
        if not hasattr(self, "transformer"):
            raise JaqalError("Cannot call current_pos before visit")
        return self.transformer.current_pos

    ##
    # Token-level methods
    #

    def visit_identifier(self, identifier_string):
        return str(identifier_string)

    def visit_signed_number(self, string):
        if "." in string or "e" in string or "E" in string:
            return float(string)
        else:
            return int(string)

    def visit_number(self, string):
        if "." in string or "e" in string or "E" in string:
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
    def visit_usepulses_statement(self, identifier, objects):
        """Visit a usepulses statement. The identifier is the name of the
        module to import (possibly with namespaces). objects is either None, all,
        or a list of identifiers. None means the usepulses was imported with its
        namespace. all (the Python built-in function) means all objects in that
        namespace were imported into the global namespace. Finally, a list of
        identifiers means those identifiers are pulled into the global namespace."""
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

    def visit_macro_header(self, name, arguments):
        """Visit the head of a macro. This override is optional as the information will be passed to
        visit_macro_definition."""
        pass

    def visit_macro_gate_block(self, block):
        """Visit the block of a macro. This override is optional as the information will be passed to
        visit_macro_definition."""
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
    def visit_array_element_qual(self, identifier, index):
        """Visit an array, dereferenced to a single element. The index is either an identifier or integer. The
        identifier in this case is a qualified identifier."""
        pass

    @abstractmethod
    def visit_array_slice(self, identifier, index_slice):
        """Visit an array dereferenced by slice, as used in the map statement. The identifier is the name of the
        existing array, and index_slice is a Python slice object. None represents the lack of a bound, an integer a
        definite bound, and a string is an identifier used as that bound."""
        pass

    @abstractmethod
    def visit_let_identifier(self, identifier):
        """Visit an identifier that can only exist if it was previously declared by a let statement."""
        pass

    @abstractmethod
    def visit_let_or_map_identifier(self, identifier):
        """Visit an identifier that must be declared in either a let or map statement."""
        pass

    @abstractmethod
    def visit_qualified_identifier(self, names):
        """Visit an identifier qualified with zero or more namespaces. The identifier's name is in the most-significant
        index."""
        pass


class TreeManipulators:

    ##
    # New methods to construct parts of the tree
    #

    @staticmethod
    def make_program(header_statements, body_statements):
        return Tree(
            "start",
            [
                Tree("header_statements", header_statements),
                Tree("body_statements", body_statements),
            ],
        )

    @staticmethod
    def make_register_statement(array_declaration):
        return Tree("register_statement", [array_declaration])

    @staticmethod
    def make_map_statement(target, source):
        return Tree("map_statement", [target, source])

    @staticmethod
    def make_let_statement(identifier, number):
        return Tree("let_statement", [identifier, number])

    @staticmethod
    def make_usepulses_statement(identifier, objects):
        if objects is not all:
            raise JaqalError("Only from foo usepulses * implemented")
        from_clause = Tree("from_clause", [identifier])
        all_module = Tree("all_module", [])
        return Tree("usepulses_statement", [from_clause, all_module])

    @staticmethod
    def make_gate_statement(gate_name, gate_args):
        return Tree("gate_statement", [gate_name] + gate_args)

    @classmethod
    def make_macro_definition(cls, name, arguments, block):
        macro_header = cls.make_macro_header(name, arguments)
        macro_gate_block = cls.make_macro_gate_block(block)
        return Tree("macro_definition", [macro_header, macro_gate_block])

    @staticmethod
    def make_macro_header(name, arguments):
        return Tree("macro_header", [name] + arguments)

    @classmethod
    def make_macro_gate_block(cls, block):
        if cls.is_macro_gate_block(block):
            # This allows use for much more transparent uses of this method and allows other methods to ignore
            # the exact form of the gate block they receive, which in term makes them more flexible.
            return block
        return Tree("macro_gate_block", [block])

    @classmethod
    def make_loop_statement(cls, repetition_count, block):
        return Tree(
            "loop_statement", [cls.enforce_integer_if_numeric(repetition_count), block]
        )

    @staticmethod
    def make_sequential_gate_block(statements):
        return Tree("sequential_gate_block", statements)

    @staticmethod
    def make_parallel_gate_block(statements):
        return Tree("parallel_gate_block", statements)

    @classmethod
    def make_array_declaration(cls, identifier, size):
        return Tree(
            "array_declaration", [identifier, cls.enforce_integer_if_numeric(size)]
        )

    @classmethod
    def make_array_element(cls, identifier, index):
        return Tree(
            "array_element", [identifier, cls.enforce_signed_integer_if_numeric(index)]
        )

    @classmethod
    def make_array_element_qual(cls, identifier, index):
        return Tree(
            "array_element_qual",
            [identifier, cls.enforce_signed_integer_if_numeric(index)],
        )

    @classmethod
    def make_array_slice(cls, identifier, index_slice):
        index_start_children = (
            [cls.enforce_signed_integer_if_numeric(index_slice.start)]
            if index_slice.start is not None
            else []
        )
        index_stop_children = (
            [cls.enforce_signed_integer_if_numeric(index_slice.stop)]
            if index_slice.stop is not None
            else []
        )
        index_step_children = (
            [cls.enforce_signed_integer_if_numeric(index_slice.step)]
            if index_slice.step is not None
            else []
        )

        index_start = Tree("array_slice_start", index_start_children)
        index_stop = Tree("array_slice_stop", index_stop_children)
        index_step = Tree("array_slice_step", index_step_children)

        indices = [
            index
            for index in [index_start, index_stop, index_step]
            if index is not None
        ]

        return Tree("array_slice", [identifier] + indices)

    @staticmethod
    def make_let_identifier(identifier):
        return Tree("let_identifier", [identifier])

    @staticmethod
    def make_let_or_map_identifier(identifier):
        return Tree("let_or_map_identifier", [identifier])

    @staticmethod
    def make_let_or_integer(identifier):
        return Tree("let_or_integer", [identifier])

    @classmethod
    def make_qualified_identifier(cls, names):
        children = []
        for name in names:
            if cls.is_identifier(name):
                children.append(name)
            else:
                children.append(cls.make_identifier(name))
        return Tree("qualified_identifier", children)

    @staticmethod
    def make_identifier(identifier_string):
        return Token("IDENTIFIER", identifier_string)

    @staticmethod
    def make_signed_number(number):
        if not isinstance(number, float) and not isinstance(number, int):
            raise JaqalError(f"Expected number, found {number}")
        return Token("SIGNED_NUMBER", str(number))

    @staticmethod
    def make_number(number):
        if (
            not isinstance(number, float) and not isinstance(number, int)
        ) or number < 0:
            raise JaqalError(f"Expected non-negative number, found {number}")
        return Token("NUMBER", str(number))

    @staticmethod
    def make_integer(number):
        if not isinstance(number, int) or number < 0:
            raise JaqalError(f"Expected non-negative integer, found {number}")
        return Token("INTEGER", str(number))

    @staticmethod
    def make_signed_integer(number):
        if not isinstance(number, int):
            raise JaqalError(f"Expected integer, found {number}")
        return Token("SIGNED_INTEGER", str(number))

    @classmethod
    def enforce_integer_if_numeric(cls, number):
        if cls.is_integer(number):
            return number
        elif (
            cls.is_signed_integer(number)
            or cls.is_number(number)
            or cls.is_signed_number(number)
        ):
            # A signed number token can be converted to a float but not an int, so we have a workaround here.
            if float(number) < 0 or float(number) != int(float(number)):
                raise JaqalError(f"Expected integer, found {number}")
            return cls.make_integer(int(float(number)))
        else:
            # Likely an identifier
            return number

    @classmethod
    def enforce_signed_integer_if_numeric(cls, number):
        if cls.is_signed_integer(number):
            return number
        elif cls.is_integer(number):
            return cls.make_signed_integer(int(number))
        elif cls.is_number(number) or cls.is_signed_number(number):
            # A signed number token can be converted to a float but not an int, so we have a workaround here.
            if float(number) != int(float(number)):
                raise JaqalError(f"Expected signed integer, found {number}")
            return cls.make_signed_integer(int(float(number)))
        else:
            return number

    ##
    # New methods to check if a portion of a tree or token is of a given type
    #

    @classmethod
    def is_program(cls, tree):
        return cls._is_tree(tree, "start")

    @classmethod
    def is_register_statement(cls, tree):
        return cls._is_tree(tree, "register_statement")

    @classmethod
    def is_map_statement(cls, tree):
        return cls._is_tree(tree, "map_statement")

    @classmethod
    def is_let_statement(cls, tree):
        return cls._is_tree(tree, "let_statement")

    @classmethod
    def is_body_statements(cls, tree):
        # Note: The visitor would not visit this directly but as part of visiting the whole program
        return cls._is_tree(tree, "body_statements")

    @classmethod
    def is_header_statements(cls, tree):
        return cls._is_tree(tree, "header_statements")

    @classmethod
    def is_gate_statement(cls, tree):
        return cls._is_tree(tree, "gate_statement")

    @classmethod
    def is_macro_definition(cls, tree):
        return cls._is_tree(tree, "macro_definition")

    @classmethod
    def is_macro_header(cls, tree):
        return cls._is_tree(tree, "macro_header")

    @classmethod
    def is_macro_gate_block(cls, tree):
        return cls._is_tree(tree, "macro_gate_block")

    @classmethod
    def is_loop_statement(cls, tree):
        return cls._is_tree(tree, "loop_statement")

    @classmethod
    def is_sequential_gate_block(cls, tree):
        return cls._is_tree(tree, "sequential_gate_block")

    @classmethod
    def is_parallel_gate_block(cls, tree):
        return cls._is_tree(tree, "parallel_gate_block")

    @classmethod
    def is_array_declaration(cls, tree):
        return cls._is_tree(tree, "array_declaration")

    @classmethod
    def is_array_element(cls, tree):
        return cls._is_tree(tree, "array_element")

    @classmethod
    def is_array_slice(cls, tree):
        return cls._is_tree(tree, "array_slice")

    @classmethod
    def is_let_identifier(cls, tree):
        return cls._is_tree(tree, "let_identifier")

    @classmethod
    def is_let_or_map_identifier(cls, tree):
        return cls._is_tree(tree, "let_or_map_identifier")

    @classmethod
    def is_identifier(cls, token):
        return cls._is_token(token, "IDENTIFIER")

    @classmethod
    def is_qualified_identifier(cls, tree):
        return cls._is_tree(tree, "qualified_identifier")

    @classmethod
    def is_signed_number(cls, token):
        return cls._is_token(token, "SIGNED_NUMBER")

    @classmethod
    def is_number(cls, token):
        return cls._is_token(token, "NUMBER")

    @classmethod
    def is_integer(cls, token):
        return cls._is_token(token, "INTEGER")

    @classmethod
    def is_signed_integer(cls, token):
        return cls._is_token(token, "SIGNED_INTEGER")

    @classmethod
    def _is_tree(cls, tree, data):
        return cls.is_tree(tree) and tree.data == data

    @classmethod
    def _is_token(cls, token, data):
        return cls.is_token(token) and token.type == data

    @staticmethod
    def is_tree(tree):
        return isinstance(tree, Tree)

    @staticmethod
    def is_token(token):
        return isinstance(token, Token)

    ##
    # Deconstruct trees and tokens into their parts, used to go top down instead of (actually in addition to) bottom-up
    #

    @staticmethod
    def deconstruct_sequential_gate_block(tree):
        return tree.children

    @staticmethod
    def deconstruct_parallel_gate_block(tree):
        return tree.children

    @staticmethod
    def deconstruct_macro_gate_block(tree):
        """Return the sequential or parallel gate block inside a macro gate block."""
        return tree.children[0]

    @staticmethod
    def deconstruct_array_declaration(tree):
        """Return the portion of the tree that is the identifier and the size."""
        identifier, size = tree.children
        return identifier, size

    @staticmethod
    def deconstruct_array_slice(tree):
        """Return the portion of the tree that is the identifier and a 3-tuple with tokens representing the slice."""
        identifier, slice_start, slice_stop, slice_step = tree.children

        slice_start = slice_start.children[0] if slice_start.children else None
        slice_stop = slice_stop.children[0] if slice_stop.children else None
        slice_step = slice_step.children[0] if slice_step.children else None

        return identifier, (slice_start, slice_stop, slice_step)

    @staticmethod
    def deconstruct_array_element(tree):
        """Return the portion of the tree that is the identifier and the index."""
        identifier, index = tree.children
        return identifier, index

    @classmethod
    def deconstruct_let_or_map_identifier(cls, tree):
        """Return a qualified identifier from a let-or-map identifier."""
        assert len(tree.children) == 1
        return cls.extract_qualified_identifier(tree.children[0])

    @classmethod
    def deconstruct_let_identifier(cls, tree):
        """Return a qualified identifier from a let identifier."""
        assert len(tree.children) == 1
        return cls.extract_qualified_identifier(tree.children[0])

    @staticmethod
    def extract_qualified_identifier(tree):
        """Return a qualified identifier as a tuple of strings."""
        return Identifier(str(child) for child in tree.children)

    @staticmethod
    def extract_identifier(token):
        """Return an identifier as an Identifier object."""
        return Identifier.parse(token)

    @staticmethod
    def extract_integer(token):
        return int(token)

    @staticmethod
    def extract_signed_integer(token):
        return int(token)

    @staticmethod
    def extract_number(token):
        return float(token)

    @staticmethod
    def extract_signed_number(token):
        return float(token)

    @classmethod
    def extract_token(cls, token):
        """Figure out what the token is and call the appropriate extract method."""
        if cls.is_identifier(token):
            return cls.extract_identifier(token)
        elif cls.is_integer(token):
            return cls.extract_integer(token)
        elif cls.is_signed_integer(token):
            return cls.extract_signed_integer(token)
        elif cls.is_number(token):
            return cls.extract_number(token)
        elif cls.is_signed_number(token):
            return cls.extract_signed_number(token)
        else:
            raise JaqalError(f"Unknown token: {token}")


class TreeRewriteVisitor(ParseTreeVisitor, TreeManipulators):
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

    def visit_usepulses_statement(self, identifier, objects):
        return self.make_usepulses_statement(identifier, objects)

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

    def visit_array_element_qual(self, identifier, index):
        return self.make_array_element_qual(identifier, index)

    def visit_array_slice(self, identifier, index_slice):
        return self.make_array_slice(identifier, index_slice)

    def visit_let_identifier(self, identifier):
        return self.make_let_identifier(identifier)

    def visit_let_or_map_identifier(self, identifier):
        return self.make_let_or_map_identifier(identifier)

    def visit_qualified_identifier(self, names):
        return self.make_qualified_identifier(names)


class JaqalParseError(JaqalError):
    """
    Bases: :exc:`jaqalpaq.JaqalError`

    Represents parse errors, with :attr:`line` and :attr:`column` properties denoting
    where in the input the error occurred.
    """

    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column

    def __str__(self):
        return f"{self.message}: line {self.line} column {self.column}"
