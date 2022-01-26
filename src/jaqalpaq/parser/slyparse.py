# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.

from collections import deque
from os import devnull

from sly import Lexer, Parser

from .identifier import Identifier
from jaqalpaq.error import JaqalError
import sly.yacc

# We attempt to ``monkeypatch'' the sly library to remove some expensive checks.
# This has no side effects if the JaqalPaq parser is working correctly and sly has
# not changed.
#
# If the API changes, we present a warning --- that warning can be disabled by
# setting this to false:
_SLY_TURBO_WARNING = True


class JaqalLexer(Lexer):
    """Form lexical tokens for Jaqal."""

    literals = {"<", ">", "|", "{", "}", ";", "[", "]", ",", "*", ":"}

    tokens = {
        REG,
        MAP,
        LET,
        MACRO,
        LOOP,
        IMPORT,
        USEPULSES,
        FROM,
        AS,
        NL,
        IDENTIFIER,
        DOTIDENTIFIER,
        NUMBER,
        INT,
        BININT,
        BRANCH,
        SUBCIRCUIT,
    }

    # Ignore whitespace, but not newlines
    ignore = " \t"
    NL = r"\n+"

    # Identifiers and numbers
    IDENTIFIER = r"[a-zA-Z_](\.?[a-zA-Z0-9_])*"
    DOTIDENTIFIER = r"\.([a-zA-Z_](\.?[a-zA-Z0-9_])*)?"
    NUMBER = r"[-+]?[0-9]*\.[0-9]+([eE][-+]?[0-9]+)?"
    INT = r"[-+]?[0-9]+"
    BININT = r"'[0-1]+'"

    # Keywords
    IDENTIFIER["register"] = REG
    IDENTIFIER["map"] = MAP
    IDENTIFIER["let"] = LET
    IDENTIFIER["macro"] = MACRO
    IDENTIFIER["loop"] = LOOP
    IDENTIFIER["import"] = IMPORT
    IDENTIFIER["usepulses"] = USEPULSES
    IDENTIFIER["from"] = FROM
    IDENTIFIER["as"] = AS
    IDENTIFIER["branch"] = BRANCH
    IDENTIFIER["subcircuit"] = SUBCIRCUIT

    # Comments
    ignore_comment = r"//[^\n]*"
    # We have to get fancy since the regular expression . does not
    # match a new line
    ignore_multiline_comment = r"/\*(\n|[^\n])*\*/"

    def ignore_comment(self, token):
        self.lineno += token.value.count("\n")

    def ignore_multiline_comment(self, token):
        self.lineno += token.value.count("\n")

    def NL(self, token):
        self.lineno += token.value.count("\n")
        return token

    def INT(self, token):
        token.value = int(token.value)
        return token

    def NUMBER(self, token):
        token.value = float(token.value)
        return token

    def BININT(self, token):
        token.value = int(token.value[1:-1], base=2)
        return token


class JaqalParser(Parser):
    """Parse Jaqal into core types."""

    def __init__(self, source_text=None, source="<string>", header_only=False):
        """Create a new Jaqal parser.

        :param str source_text: The original source. Optional, but
        enables column tracking in error messages.

        :param str source: The source of the Jaqal text, e.g. the file name.

        :param bool header_only: Whether to stop parsing once the
        header is finished.

        """
        # This is set to true when the first body statement is
        # reached. At that point seeing a header statement is an
        # error.
        self._in_body = False

        self._source_text = source_text

        self._source = source

        self._last_line = 1
        self._last_index = 1

        self._header_only = header_only

        # Store all top-level statements in an attribute so that we
        # can interrupt parsing midway through a file and return
        # partial results.
        self.top_sexpression = ["circuit"]

        # A dictionary populated with the results of usepulses
        # statements.
        self.usepulses = {}

    tokens = JaqalLexer.tokens

    @_("seqpad top_statements")
    def start(self, tree):
        return self.top_sexpression

    @_("")
    def empty(self, _tree):
        pass

    # Top-level statements

    @_("top_statement seqsep top_statements")
    def top_statements(self, tree):
        pass

    @_("top_statement")
    def top_statements(self, tree):
        pass

    @_("empty")
    def top_statements(self, _tree):
        pass

    # Define what a top-level statement is. Note that these are both
    # header and body statements, but we will forbid header statements
    # after body statements in the rules.

    @_(
        "register_statement",
        "let_statement",
        "map_statement",
        "usepulses_statement",
        "import_statement",
    )
    def top_statement(self, tree):
        if self._in_body:
            self.raise_error(f"Header statement {tree[0]} found after body statement")
        self.top_sexpression.append(tree[0])

    @_(
        "gate_statement",
        "parallel_gate_block",
        "sequential_gate_block",
        "subcircuit_gate_block",
        "loop_statement",
        "macro_definition",
        "branch_statement",
    )
    def top_statement(self, tree):
        if self._header_only:
            raise HeaderParsingDone()
        self._in_body = True
        self.top_sexpression.append(tree[0])

    # Define what statements are allowed in sequential blocks.

    @_(
        "gate_statement",
        "parallel_gate_block",
        "loop_statement",
        "subcircuit_gate_block",
    )
    def inner_seq_statement(self, tree):
        # No need to set self._in_body as we've definitely already set
        # it.
        return tree[0]

    # Define what statements are allowed in parallel blocks

    @_("gate_statement", "sequential_gate_block")
    def inner_par_statement(self, tree):
        return tree[0]

    # Register statement

    @_('REG IDENTIFIER "[" let_or_int "]"')
    def register_statement(self, tree):
        self.set_pos(tree)
        if isinstance(tree.let_or_int, int) and tree.let_or_int <= 0:
            self.raise_error(
                f"Defining register {tree.IDENTIFIER}: Invalid register size {tree.let_or_int}"
            )
        return ["register", tree.IDENTIFIER, tree.let_or_int]

    # Let statement

    @_("LET IDENTIFIER NUMBER", "LET IDENTIFIER INT")
    def let_statement(self, tree):
        self.set_pos(tree)
        return ["let", tree.IDENTIFIER, tree[2]]

    # Map statement

    @_("MAP IDENTIFIER map_source")
    def map_statement(self, tree):
        self.set_pos(tree)
        return ["map", tree.IDENTIFIER, *tree.map_source]

    @_("IDENTIFIER")
    def map_source(self, tree):
        return [tree.IDENTIFIER]

    @_('IDENTIFIER "[" slice_or_index "]"')
    def map_source(self, tree):
        return [tree.IDENTIFIER, *tree.slice_or_index]

    @_("let_or_int")
    def slice_or_index(self, tree):
        return [tree.let_or_int]

    @_("slice_start slice_stop slice_step")
    def slice_or_index(self, tree):
        return [tree.slice_start, tree.slice_stop, tree.slice_step]

    @_('let_or_int ":"')
    def slice_start(self, tree):
        return tree.let_or_int

    @_('":"')
    def slice_start(self, tree):
        return None

    @_("let_or_int")
    def slice_stop(self, tree):
        return tree.let_or_int

    @_("empty")
    def slice_stop(self, tree):
        return None

    @_('":" let_or_int')
    def slice_step(self, tree):
        return tree.let_or_int

    @_("empty")
    def slice_step(self, tree):
        return None

    # Usepulses statement

    @_('FROM IDENTIFIER USEPULSES "*"')
    def usepulses_statement(self, tree):
        self.set_pos(tree)
        ident = Identifier.parse(tree.IDENTIFIER)
        self.usepulses[ident] = all
        return ["usepulses", ident, "*"]

    @_('FROM DOTIDENTIFIER USEPULSES "*"')
    def usepulses_statement(self, tree):
        self.set_pos(tree)
        ident = Identifier.parse(tree.DOTIDENTIFIER)
        self.usepulses[ident] = all
        return ["usepulses", ident, "*"]

    # Import statement

    @_("IMPORT IDENTIFIER AS IDENTIFIER")
    def import_statement(self, tree):
        # This rule exists so that "IMPORT" and "AS" are not unused
        # tokens.
        self.raise_error(f"Import statement not yet implemented")

    # Gate statement

    @_("IDENTIFIER gate_args")
    def gate_statement(self, tree):
        # self.set_pos(tree)
        return ["gate", tree.IDENTIFIER, *tree.gate_args]

    @_("gate_arg gate_args")
    def gate_args(self, tree):
        args = tree.gate_args
        args.appendleft(tree.gate_arg)
        return args

    @_("empty")
    def gate_args(self, _tree):
        return deque()

    @_("IDENTIFIER", "NUMBER", "INT")
    def gate_arg(self, tree):
        return tree[0]

    @_('IDENTIFIER "[" IDENTIFIER "]"', 'IDENTIFIER "[" INT "]"')
    def gate_arg(self, tree):
        return ("array_item", tree[0], tree[2])

    # Loop statement

    @_("LOOP let_or_int gate_block")
    def loop_statement(self, tree):
        # self.set_pos(tree)
        return ["loop", tree.let_or_int, tree.gate_block]

    # Branch statement

    @_("BRANCH branch_block")
    def branch_statement(self, tree):
        return ["branch", *tree.branch_block]

    # Case statement

    @_('BININT ":" gate_block')
    def case_statement(self, tree):
        return ["case", tree.BININT, tree.gate_block]

    # macro definition

    @_("MACRO macro_args gate_block")
    def macro_definition(self, tree):
        # self.set_pos(tree)
        return ["macro", *tree.macro_args, tree.gate_block]

    @_("IDENTIFIER macro_args")
    def macro_args(self, tree):
        return [tree.IDENTIFIER, *tree.macro_args]

    @_("IDENTIFIER")
    def macro_args(self, tree):
        # Note macro_args has no empty case as we always need a macro name.
        return [tree.IDENTIFIER]

    @_("sequential_gate_block", "parallel_gate_block")
    def gate_block(self, tree):
        return tree[0]

    # Sequential block

    @_("curly_brace_block")
    def sequential_gate_block(self, tree):
        ret = tree.curly_brace_block
        ret.appendleft("sequential_block")
        return list(ret)

    @_('"{" seqpad sequential_statements "}"')
    def curly_brace_block(self, tree):
        ret = tree.sequential_statements
        return ret

    @_("inner_seq_statement seqsep sequential_statements")
    def sequential_statements(self, tree):
        ret = tree.sequential_statements
        ret.appendleft(tree.inner_seq_statement)
        return ret

    @_("inner_seq_statement")
    def sequential_statements(self, tree):
        ret = deque([tree.inner_seq_statement])
        return ret

    @_("empty")
    def sequential_statements(self, _tree):
        return deque()

    # Parallel block

    @_('"<" parpad parallel_statements ">"')
    def parallel_gate_block(self, tree):
        # self.set_pos(tree)
        ret = tree.parallel_statements
        ret.appendleft("parallel_block")
        return list(ret)

    @_("inner_par_statement parsep parallel_statements")
    def parallel_statements(self, tree):
        ret = tree.parallel_statements
        ret.appendleft(tree.inner_par_statement)
        return ret

    @_("inner_par_statement")
    def parallel_statements(self, tree):
        return deque([tree.inner_par_statement])

    @_("empty")
    def parallel_statements(self, tree):
        return deque()

    # Subcircuit block

    @_("SUBCIRCUIT curly_brace_block")
    def subcircuit_gate_block(self, tree):
        ret = tree.curly_brace_block
        ret.appendleft("")  # represent empty iteration count
        ret.appendleft("subcircuit_block")
        return list(ret)

    @_("SUBCIRCUIT let_or_int curly_brace_block")
    def subcircuit_gate_block(self, tree):
        ret = tree.curly_brace_block
        ret.appendleft(tree.let_or_int)
        ret.appendleft("subcircuit_block")
        return list(ret)

    # Branches

    @_('"{" seqpad case_statements "}"')
    def branch_block(self, tree):
        ret = tree.case_statements
        # ret.appendleft("branch")
        return ret

    @_("case_statement seqsep case_statements")
    def case_statements(self, tree):
        ret = tree.case_statements
        ret.appendleft(tree.case_statement)
        return ret

    @_("case_statement")
    def case_statements(self, tree):
        return deque([tree.case_statement])

    @_("empty")
    def case_statements(self, _tree):
        return deque()

    # Common rules

    @_("INT", "IDENTIFIER")
    def let_or_int(self, tree):
        return tree[0]

    # Separators

    @_("NL", "NL seqsep", '";"', '";" seqsep')
    def seqsep(self, _tree):
        pass

    @_("NL seqpad", '";" seqpad', "empty")
    def seqpad(self, _tree):
        pass

    @_("NL", "NL parsep", '"|"', '"|" parsep')
    def parsep(self, _tree):
        pass

    @_("NL parpad", '"|" parpad', "empty")
    def parpad(self, _tree):
        pass

    # Error Handling

    def error(self, token):
        """Standard callback by the parser for erroneous tokens."""
        if token is not None:
            line = token.lineno
            col = self.compute_col(token.index)
        else:
            line = "EOF"
            col = 0
        raise JaqalParseError(self._source, line, col, f"At token `{token.value}`")

    def raise_error(self, message):
        """Common method for when errors come up not in the grammar but in the
        rules."""

        line = self._last_line
        col = self.compute_col()
        raise JaqalParseError(self._source, line, col, message)

    def compute_col(self, index=None):
        """Return the column within a line of the given index, or 0 if we
        don't have the original text."""

        if self._source_text is None:
            return 0

        index = index or self._last_index

        ncol = self._source_text.rfind("\n", 0, index)

        return index - ncol

    def set_pos(self, tree):
        """Register the current parser position to be used by the error
        handler if necessary."""
        if hasattr(tree, "lineno"):
            self._last_line = tree.lineno
            self._last_index = tree.index


class JaqalParseError(JaqalError):
    """An error thrown by the parser or lexer."""

    def __init__(self, source, line, column, msg):
        """Create a standardized format for parse errors.

        :param str source: The source of the Jaqal text, e.g. the file name.
        :param int line: The line number, starting at 1, of the error.
        :param int column: The column number, starting at 1, of the error.
        :param str msg: The human-readable message describing the error.
        """
        super().__init__(f"{source}:{line}:{column}: error: {msg}")
        self.line = line
        self.column = column


def _monkeypatch_sly():
    """Monkey-Patch!!! This method only serves to make sure the library
    user (us) doesn't set the value for a production rule. We
    don't. On large files the savings are substantial.

    """

    if not hasattr(_monkeypatch_sly, "_called_once"):
        _monkeypatch_sly._called_once = True
    else:
        return

    try:
        del sly.yacc.YaccProduction.__setattr__
    except AttributeError:
        if _SLY_TURBO_WARNING:
            print("Warning: An internal sly behavior has changed, which may result")
            print("slower parsing of large Jaqal source files.  To disable this, ")
            print("jaqalpaq.core.parser.slyparse._SLY_TURBO_WARNING to False.")


class HeaderParsingDone(Exception):
    """Exception raised to indicate that the header is complete. The
    results can then be pulled from the 'top_sexpression' attribute of the
    parser."""

    pass
