from unittest import TestCase
from numbers import Number

from jaqalpaq.core import (
    GateDefinition,
    Register,
    Circuit,
    Parameter,
    BlockStatement,
    LoopStatement,
    Macro,
    Constant,
    NamedQubit,
    AnnotatedValue,
)
from jaqalpaq.core.branch import BranchStatement, CaseStatement
from jaqalpaq.parser import parse_jaqal_string, JaqalParseError
from jaqalpaq.parser.parser import parse_jaqal_string_header
from jaqalpaq.parser.identifier import Identifier
from jaqalpaq.error import JaqalError


class ParserTester(TestCase):
    def setUp(self):
        self.gate_definitions = {}
        self.registers = {}

    def test_gate_statement_no_args(self):
        text = "foo"
        exp_result = self.make_circuit(gates=[self.make_gate("foo")])
        self.run_test(text, exp_result)

    def test_gate_statement_numeric_arg(self):
        text = "foo 3.14"
        exp_result = self.make_circuit(gates=[self.make_gate("foo", 3.14)])
        self.run_test(text, exp_result)

    def test_gate_statement_qubit_arg(self):
        text = "register r[3]; foo r[1]"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            gates=[self.make_gate("foo", ("r", 1))],
        )
        self.run_test(text, exp_result)

    def test_top_level_sequential_gate_block(self):
        text = "{foo}"
        exp_result = self.make_circuit(
            gates=[self.make_sequential_gate_block(self.make_gate("foo"))]
        )
        self.run_test(text, exp_result)

    def test_forbid_multiple_registers(self):
        text = "register r[3]; register q[7]"
        with self.assertRaises(JaqalError):
            parse_jaqal_string(text, autoload_pulses=False)

    def test_let_float(self):
        """Test a let constant that is a floating point value."""
        text = "let a 3.14; foo a"
        exp_result = self.make_circuit(
            constants={"a": self.make_constant("a", 3.14)},
            gates=[self.make_gate("foo", self.make_constant("a", 3.14))],
        )
        self.run_test(text, exp_result)

    def test_let_override(self):
        text = "register r[3]; let a 1; let b 3.14; foo r[a] b"
        exp_result = self.make_circuit(
            constants={
                "a": self.make_constant("a", 1),
                "b": self.make_constant("b", 3.14),
            },
            registers={"r": self.make_register("r", 3)},
            gates=[self.make_gate("foo", ("r", 0), 1.41)],
        )
        override_dict = {"a": 0, "b": 1.41}
        self.run_test(text, exp_result, override_dict=override_dict, expand_let=True)

    def test_let_as_register_index(self):
        """Test a let-constant used as a register index and not expanded."""
        text = "register r[3]; let a 1; foo r[a]"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            constants={"a": self.make_constant("a", 1)},
            gates=[self.make_gate("foo", ("r", self.make_constant("a", 1)))],
        )
        self.run_test(text, exp_result)

    def test_let_as_map_index(self):
        """Test a let-constant used as a map index and not expanded."""
        text = "register r[3]; map q r; let a 1; foo q[a]"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            maps={"q": self.make_map("q", "r", None)},
            constants={"a": self.make_constant("a", 1)},
            gates=[self.make_gate("foo", ("q", self.make_constant("a", 1)))],
        )
        self.run_test(text, exp_result)

    def test_let_as_map_range(self):
        """Test a let-constant used as an element in the slice defining a map that is not expanded."""
        text = "register r[3]; let a 1; map q r[a:]"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            constants={"a": self.make_constant("a", 1)},
            maps={"q": self.make_map("q", "r", (self.make_constant("a", 1), 3, 1))},
            gates=[],
        )
        self.run_test(text, exp_result)

    def test_let_in_register_size(self):
        """Test a let-constant used as the size of a register."""
        text = "let a 5; register r[a]"
        exp_result = self.make_circuit(
            constants={"a": self.make_constant("a", 5)},
            registers={"r": self.make_register("r", self.make_constant("a", 5))},
            gates=[],
        )
        self.run_test(text, exp_result)

    def test_macro_param_shadowing_let_constant(self):
        """Test a let-constant with the same name as a macro parameter. No expansion."""
        text = "register r[3]; let a 1; macro foo a { g a }"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            constants={"a": self.make_constant("a", 1)},
            macros={"foo": self.make_macro("foo", ["a"], self.make_gate("g", "a"))},
            gates=[],
        )
        self.run_test(text, exp_result)

    def test_parallel_block(self):
        text = "<foo | bar>"
        exp_result = self.make_circuit(
            gates=[
                self.make_parallel_gate_block(
                    self.make_gate("foo"), self.make_gate("bar")
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_loop(self):
        text = "loop 32 { foo; bar }"
        exp_result = self.make_circuit(
            gates=[
                self.make_loop(self.make_gate("foo"), self.make_gate("bar"), count=32)
            ]
        )
        self.run_test(text, exp_result)

    def test_sequential_block_in_parallel_block(self):
        text = "< p | { foo; bar }>"
        exp_result = self.make_circuit(
            gates=[
                self.make_parallel_gate_block(
                    self.make_gate("p"),
                    self.make_sequential_gate_block(
                        self.make_gate("foo"), self.make_gate("bar")
                    ),
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_subcircuit_block_no_iterations(self):
        text = "subcircuit { foo; bar }"
        exp_result = self.make_circuit(
            gates=[
                self.make_subcircuit_gate_block(
                    1, self.make_gate("foo"), self.make_gate("bar")
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_subcircuit_block_int_iterations(self):
        text = "subcircuit 300 { foo; bar }"
        exp_result = self.make_circuit(
            gates=[
                self.make_subcircuit_gate_block(
                    300, self.make_gate("foo"), self.make_gate("bar")
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_subcircuit_block_let_iterations(self):
        text = "let a 500; subcircuit a { foo; bar }"
        a = self.make_constant("a", 500)
        exp_result = self.make_circuit(
            constants={"a": a},
            gates=[
                self.make_subcircuit_gate_block(
                    a, self.make_gate("foo"), self.make_gate("bar")
                )
            ],
        )
        self.run_test(text, exp_result)

    def test_subcircuit_block_in_parallel(self):
        text = "<subcircuit { foo; bar }>"
        with self.assertRaises(JaqalError):
            parse_jaqal_string(text, inject_pulses=None, autoload_pulses=False)

    def test_subcircuit_block_in_subcircuit(self):
        text = "subcircuit { subcircuit { foo; bar } }"
        with self.assertRaises(JaqalError):
            parse_jaqal_string(text, inject_pulses=None, autoload_pulses=False)

    def test_subcircuit_indirectly_in_parallel(self):
        text = "< { subcircuit { foo } } >"
        with self.assertRaises(JaqalError):
            parse_jaqal_string(text, inject_pulses=None, autoload_pulses=False)

    def test_subcircuit_indirectly_in_subcircuit(self):
        text = "subcircuit { loop 1 { subcircuit { foo } } }"
        with self.assertRaises(JaqalError):
            parse_jaqal_string(text, inject_pulses=None, autoload_pulses=False)

    def test_subcircuit_in_macro(self):
        text = "macro foo a b {\n  subcircuit {\n    bar\n  }\n}"
        exp_result = self.make_circuit(
            macros={
                "foo": self.make_macro(
                    "foo",
                    ["a", "b"],
                    self.make_subcircuit_gate_block(
                        1,
                        self.make_gate("bar"),
                    ),
                ),
            },
            gates=[],
        )
        self.run_test(text, exp_result)

    def test_subcircuit_in_loop(self):
        text = "loop 2 {\n  subcircuit 3 {\n    foo 4\n  }\n}\n"
        exp_result = self.make_circuit(
            gates=[
                self.make_loop(
                    self.make_subcircuit_gate_block(
                        3,
                        self.make_gate("foo", 4),
                    ),
                    count=2,
                ),
            ],
        )
        self.run_test(text, exp_result)

    def test_registers(self):
        """Test that the registers are properly read."""
        text = "register r[7]"
        exp_result = self.make_circuit(
            gates=[], registers={"r": self.make_register("r", 7)}
        )
        self.run_test(text, exp_result=exp_result)

    def test_macro_definition_no_expand(self):
        """Test parsing macro definitions without expanding them."""
        text = "macro foo a { g a }; foo 1.5"
        exp_result = self.make_circuit(
            gates=[self.make_gate("foo", 1.5)],
            macros={"foo": self.make_macro("foo", ["a"], self.make_gate("g", "a"))},
        )
        self.run_test(text, exp_result)

    def test_macro_definition_expand(self):
        """Test parsing macro definitions and expanding them."""
        text = "macro foo a { g a }; foo 1.5"
        exp_result = self.make_circuit(
            gates=[self.make_gate("g", 1.5)],
            # Even though we expand macros, we are not stripping the metadata,
            # so the definition will still be there.
            macros={"foo": self.make_macro("foo", ["a"], self.make_gate("g", "a"))},
        )
        self.run_test(text, exp_result, expand_macro=True)

    def test_let_no_resolve(self):
        """Test parsing a let statement"""
        text = "let a 2; foo a"
        exp_result = self.make_circuit(
            gates=[self.make_gate("foo", self.make_constant("a", 2))],
            constants={"a": self.make_constant("a", 2)},
        )
        self.run_test(text, exp_result)

    def test_let_resolve(self):
        """Test parsing a let statement and resolving it."""
        text = "let a 2; foo a"
        exp_result = self.make_circuit(
            gates=[self.make_gate("foo", 2)],
            constants={"a": self.make_constant("a", 2)},
        )
        self.run_test(text, exp_result, expand_let=True)

    def test_map_no_resolve(self):
        """Test parsing a map statement."""
        text = "register r[3]; map q r[1:]; foo q[0]"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            maps={"q": self.make_map("q", "r", (1, 3, 1))},
            gates=[self.make_gate("foo", ("q", 0))],
        )
        self.run_test(text, exp_result)

    def test_map_single_qubit_no_resolve(self):
        text = "register r[3]; map q r[1]; foo q"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            maps={"q": self.make_map("q", "r", 1)},
            gates=[self.make_gate("foo", self.make_named_qubit("q"))],
        )
        self.run_test(text, exp_result)

    def test_map_resolve(self):
        """Test parsing a map statement and resolving it."""
        text = "register r[3]; map q r[1:]; foo q[0]"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            maps={"q": self.make_map("q", "r", (1, 3, 1))},
            gates=[self.make_gate("foo", ("r", 1))],
        )
        self.run_test(text, exp_result, expand_let_map=True)

    def test_map_single_qubit_resolve(self):
        text = "register r[3]; map q r[1]; foo q"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            maps={"q": self.make_map("q", "r", 1)},
            gates=[self.make_gate("foo", ("r", 1))],
        )
        self.run_test(text, exp_result, expand_let_map=True)

    def test_map_whole_register(self):
        text = "register r[3]; map q r; foo q[1]"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            maps={"q": self.make_map("q", "r", None)},
            gates=[self.make_gate("foo", ("q", 1))],
        )
        self.run_test(text, exp_result)

    def test_expand_macro_let_map_strip_metadata(self):
        """Test an example that exercises all available options."""
        text = "register r[3]; map q r; let a 2; macro foo x y { g x y }; foo q[a] 3.14"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            constants={"a": self.make_constant("a", 2)},
            maps={"q": self.make_map("q", "r", None)},
            macros={
                "foo": self.make_macro("foo", ["x", "y"], self.make_gate("g", "x", "y"))
            },
            gates=[self.make_gate("g", ("r", 2), 3.14)],
        )
        self.run_test(text, exp_result, expand_macro=True, expand_let_map=True)

    def test_no_expand_macro_let_map_leave_metadata(self):
        """Test an example that does not exercise all available options but involves features that could be."""
        text = "register r[3]; map q r; let a 2; macro foo x y { g x y }; foo q[a] 3.14"
        exp_result = self.make_circuit(
            registers={"r": self.make_register("r", 3)},
            maps={"q": self.make_map("q", "r", None)},
            constants={"a": self.make_constant("a", 2)},
            macros={
                "foo": self.make_macro("foo", ["x", "y"], self.make_gate("g", "x", "y"))
            },
            gates=[self.make_gate("foo", ("q", self.make_constant("a", 2)), 3.14)],
        )
        self.run_test(text, exp_result)

    def test_return_usepulses(self):
        text = "from MyPulses.MyClass usepulses *"
        exp_value = {"usepulses": {Identifier.parse("MyPulses.MyClass"): all}}
        _, act_value = parse_jaqal_string(
            text, return_usepulses=True, autoload_pulses=False
        )
        self.assertEqual(act_value, exp_value)

    def test_branch_statement(self):
        """Test parsing a branch statement."""
        import jaqalpaq.core.branch

        jaqalpaq.core.branch.USE_EXPERIMENTAL_BRANCH = True
        try:
            text = "branch { \n'0': { foo }\n '1': { bar } \n }"
            exp_result = self.make_circuit(
                gates=[
                    self.make_branch(
                        self.make_case(
                            0, self.make_sequential_gate_block(self.make_gate("foo"))
                        ),
                        self.make_case(
                            1, self.make_sequential_gate_block(self.make_gate("bar"))
                        ),
                    )
                ]
            )
            self.run_test(text, exp_result)
        finally:
            jaqalpaq.core.branch.USE_EXPERIMENTAL_BRANCH = False

    def test_parse_header_only(self):
        """Test parsing only the header of a jaqal string."""
        text = "let x 5\nG 1"
        exp_result = self.make_circuit(
            gates=[], constants={"x": self.make_constant("x", 5)}
        )
        act_result, _ = parse_jaqal_string_header(text, return_usepulses=True)
        self.assertEqual(exp_result, act_result)

    def test_parse_header_only_no_usepulses(self):
        """Test parsing only the header of a jaqal string without returning
        the usepulses."""
        text = "let x 5\nG 1"
        exp_result = self.make_circuit(
            gates=[], constants={"x": self.make_constant("x", 5)}
        )
        act_result = parse_jaqal_string_header(text)
        self.assertEqual(exp_result, act_result)

    ##
    # Helper methods
    #

    def run_test(
        self,
        text,
        exp_result=None,
        exp_native_gates=None,
        override_dict=None,
        native_gates=None,
        expand_macro=False,
        expand_let=False,
        expand_let_map=False,
    ):
        act_result = parse_jaqal_string(
            text,
            override_dict=override_dict,
            expand_macro=expand_macro,
            expand_let=expand_let,
            expand_let_map=expand_let_map,
            inject_pulses=native_gates,
            autoload_pulses=False,
        )
        if exp_result is not None:
            self.assertEqual(exp_result.body, act_result.body)
            self.assertEqual(exp_result.macros, act_result.macros)
            self.assertEqual(exp_result.constants, act_result.constants)
            self.assertEqual(exp_result.registers, act_result.registers)
        if exp_native_gates is not None:
            self.assertEqual(exp_native_gates, act_result.native_gates)

    @staticmethod
    def make_circuit(*, gates, registers=None, macros=None, constants=None, maps=None):
        circuit = Circuit()
        for gate in gates:
            circuit.body.statements.append(gate)
        if registers:
            circuit.registers.update(registers)
        if macros:
            circuit.macros.update(macros)
        if constants:
            circuit.constants.update(constants)
        if maps:
            circuit.registers.update(maps)
        return circuit

    def make_gate(self, name, *args, native_gates=None):
        """Make a gate that is either native or not. Don't call directly."""
        arg_objects = [self.make_argument_object(arg) for arg in args]
        if native_gates:
            gate_def = self.get_native_gate_definition(name, native_gates)
        else:
            params = [
                self.make_parameter_from_arg(idx, arg) for idx, arg in enumerate(args)
            ]
            gate_def = self.get_gate_definition(name, params)
        return gate_def(*arg_objects)

    def get_gate_definition(self, name, params):
        """Return an existing or create a new GateDefinition."""
        if name not in self.gate_definitions:
            gate_def = GateDefinition(name, params)
            self.gate_definitions[name] = gate_def
        else:
            gate_def = self.gate_definitions[name]
        return gate_def

    @staticmethod
    def get_native_gate_definition(name, native_gates):
        """Return an existing GateDefinition for a native gate or raise an exception."""
        for gate in native_gates:
            if gate.name == name:
                return gate
        raise ValueError(f"Native gate {name} not found")

    def make_argument_object(self, arg):
        """Format an argument as the GateStatement constructor expects it."""
        if isinstance(arg, Number):
            return arg
        elif isinstance(arg, tuple):
            return self.make_qubit(*arg)
        elif isinstance(arg, str):
            return Parameter(arg, None)
        elif isinstance(arg, NamedQubit):
            return arg
        elif isinstance(arg, AnnotatedValue):
            return arg
        else:
            raise TypeError(f"Cannot make an argument out of {arg}")

    def make_qubit(self, name, index):
        """Return a NamedQubit object, possibly creating a register object in the process."""
        if name not in self.registers:
            raise ValueError(f"Please define register {name}")
        else:
            return self.registers[name][index]

    def make_parameter_from_arg(self, index, arg):
        """Define a Parameter from the argument to a gate. Used to define a new GateDefinition."""
        param = self.make_parameter(index=index, kind=None)
        return param

    def make_parameter(self, name=None, index=None, kind=None):
        if name is None:
            if index is None:
                raise ValueError("Provide either name or index to Parameter")
            name = str(index)
        return Parameter(name, kind)

    def make_parallel_gate_block(self, *gates):
        return BlockStatement(parallel=True, statements=list(gates))

    def make_sequential_gate_block(self, *gates):
        return BlockStatement(parallel=False, statements=list(gates))

    def make_subcircuit_gate_block(self, iterations, *gates):
        return BlockStatement(
            subcircuit=True, iterations=iterations, statements=list(gates)
        )

    def make_loop(self, *gates, count):
        return LoopStatement(count, self.make_sequential_gate_block(*gates))

    def make_register(self, name, size):
        reg = Register(name, size)
        if name in self.registers:
            raise ValueError(f"Register {name} already exists")
        self.registers[name] = reg
        return reg

    def make_macro(self, name, parameter_names, *statements):
        """Create a new Macro object for a macro definition."""
        # Note That this only creates macros with sequential gate blocks while those with
        # parallel gate blocks are also possible.
        return Macro(
            name,
            parameters=[self.make_parameter(pname) for pname in parameter_names],
            body=self.make_sequential_gate_block(*statements),
        )

    def make_constant(self, name, value):
        return Constant(name, value)

    def make_map(self, name, reg_name, reg_indexing):
        if reg_name not in self.registers:
            raise ValueError(f"Please create register {reg_name} first")
        if isinstance(reg_indexing, tuple):
            if len(reg_indexing) != 3:
                raise ValueError(
                    f"reg_indexing must have 3 elements, found {len(reg_indexing)}"
                )
            reg_indexing = tuple(self.make_slice_component(arg) for arg in reg_indexing)
            alias_slice = slice(*reg_indexing)
            reg = Register(
                name, alias_from=self.registers[reg_name], alias_slice=alias_slice
            )
            self.registers[name] = reg
            return reg
        elif isinstance(reg_indexing, int):
            nq = NamedQubit(
                name, alias_from=self.registers[reg_name], alias_index=reg_indexing
            )
            self.registers[name] = nq
            return nq
        elif reg_indexing is None:
            reg = Register(name, alias_from=self.registers[reg_name])
            self.registers[name] = reg
            return reg
        else:
            raise ValueError(f"Bad register indexing {reg_indexing}")

    def make_slice_component(self, arg):
        if isinstance(arg, int):
            return arg
        elif isinstance(arg, str):
            return Parameter(arg, None)
        elif arg is None:
            return None
        elif isinstance(arg, AnnotatedValue):
            return arg
        else:
            raise ValueError(f"Cannot make slice component from {arg}")

    def make_named_qubit(self, name):
        """Return a named qubit that is stored as a map in the registers."""
        if name not in self.registers:
            raise ValueError(f"No entity called {name}")
        named_qubit = self.registers[name]
        if not isinstance(named_qubit, NamedQubit):
            raise TypeError(f"Register entry {name} not a named qubit")
        return named_qubit

    def make_branch(self, *cases):
        """Return a BranchStatement with the given cases."""
        return BranchStatement(list(cases))

    def make_case(self, state, block):
        """Return a CaseStatement conditioned on the given state. The state is
        represented as a str of '1' and '0's."""
        return CaseStatement(state, block)


class ErrorMessageTester(TestCase):
    """Attempt to have uniform errors in parsing."""

    def test_unexpected_token_message(self):
        try:
            text = "register r[-1]"
            parse_jaqal_string(text, autoload_pulses=False)
            self.fail("No exception raised")
        except JaqalParseError as exc:
            # Lines and columns are 1-indexed
            self.assertEqual(exc.line, 1)
            # Column for this message is the start of the word "register"
            self.assertEqual(exc.column, 1)
