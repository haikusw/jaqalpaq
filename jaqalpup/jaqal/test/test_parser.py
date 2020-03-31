from unittest import TestCase
from numbers import Number

from jaqalpup.core import (
    GateDefinition, Register, ScheduledCircuit, Parameter, BlockStatement, LoopStatement,
    NATIVE_GATES, Macro, Constant, NamedQubit, AnnotatedValue
)
from jaqalpup.jaqal.parser import parse_jaqal_string, Option


class ParserTester(TestCase):

    def setUp(self):
        self.gate_definitions = {}
        self.registers = {}

    def test_gate_statement_no_args(self):
        text = "foo"
        exp_result = self.make_circuit(gates=[self.make_gate('foo')])
        self.run_test(text, exp_result)

    def test_gate_statement_numeric_arg(self):
        text = "foo 3.14"
        exp_result = self.make_circuit(gates=[self.make_gate('foo', 3.14)])
        self.run_test(text, exp_result)

    def test_gate_statement_qubit_arg(self):
        text = "register r[3]; foo r[1]"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            gates=[
                self.make_gate('foo', ('r', 1))
            ]
        )
        self.run_test(text, exp_result)

    def test_top_level_sequential_gate_block(self):
        text = "{foo}"
        exp_result = self.make_circuit(
            gates=[
                self.make_sequential_gate_block(
                    self.make_gate('foo')
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_let_float(self):
        """Test a let constant that is a floating point value."""
        text = "let a 3.14; foo a"
        exp_result = self.make_circuit(
            constants={'a': self.make_constant('a', 3.14)},
            gates=[
                self.make_gate('foo', self.make_constant('a', 3.14))
            ]
        )
        self.run_test(text, exp_result)

    def test_let_override(self):
        text = "register r[3]; let a 1; let b 3.14; foo r[a] b"
        exp_result = self.make_circuit(
            constants={
                'a': self.make_constant('a', 1),
                'b': self.make_constant('b', 3.14)
            },
            registers={'r': self.make_register('r', 3)},
            gates=[
                self.make_gate('foo', ('r', 0), 1.41)
            ]
        )
        override_dict = {'a': 0, 'b': 1.41}
        self.run_test(text, exp_result, override_dict=override_dict,
                      option=Option.expand_let)

    def test_let_as_register_index(self):
        """Test a let-constant used as a register index and not expanded."""
        text = "register r[3]; let a 1; foo r[a]"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            constants={'a': self.make_constant('a', 1)},
            gates=[
                self.make_gate('foo', ('r', self.make_constant('a', 1)))
            ]
        )
        self.run_test(text, exp_result, option=Option.none)

    def test_let_as_map_index(self):
        """Test a let-constant used as a map index and not expanded."""
        text = "register r[3]; map q r; let a 1; foo q[a]"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            maps={'q': self.make_map('q', 'r', None)},
            constants={'a': self.make_constant('a', 1)},
            gates=[
                self.make_gate('foo', ('q', self.make_constant('a', 1)))
            ]
        )
        self.run_test(text, exp_result, option=Option.none)

    def test_let_as_map_range(self):
        """Test a let-constant used as an element in the slice defining a map that is not expanded."""
        text = "register r[3]; let a 1; map q r[a:]"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            constants={'a': self.make_constant('a', 1)},
            maps={'q': self.make_map('q', 'r', (self.make_constant('a', 1), 3, 1))},
            gates=[],
        )
        self.run_test(text, exp_result)

    def test_let_in_register_size(self):
        """Test a let-constant used as the size of a register."""
        text = "let a 5; register r[a]"
        exp_result = self.make_circuit(
            constants={'a': self.make_constant('a', 5)},
            registers={'r': self.make_register('r', self.make_constant('a', 5))},
            gates=[]
        )
        self.run_test(text, exp_result)

    def test_macro_param_shadowing_let_constant(self):
        """Test a let-constant with the same name as a macro parameter. No expansion."""
        text = "register r[3]; let a 1; macro foo a { g a }"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            constants={'a': self.make_constant('a', 1)},
            macros={
                'foo': self.make_macro(
                    'foo',
                    ['a'],
                    self.make_gate('g', 'a')
                )
            },
            gates=[]
        )
        self.run_test(text, exp_result)

    def test_parallel_block(self):
        text = "<foo | bar>"
        exp_result = self.make_circuit(
            gates=[
                self.make_parallel_gate_block(
                    self.make_gate('foo'),
                    self.make_gate('bar')
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_loop(self):
        text = "loop 32 { foo; bar }"
        exp_result = self.make_circuit(
            gates=[
                self.make_loop(
                    self.make_gate('foo'),
                    self.make_gate('bar'),
                    count=32
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_sequential_block_in_parallel_block(self):
        text = "< p | { foo; bar }>"
        exp_result = self.make_circuit(
            gates=[
                self.make_parallel_gate_block(
                    self.make_gate('p'),
                    self.make_sequential_gate_block(
                        self.make_gate('foo'),
                        self.make_gate('bar')
                    ),
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_registers(self):
        """Test that the registers are properly read."""
        text = "register r[7]"
        exp_result = self.make_circuit(
            gates=[],
            registers={'r': self.make_register('r', 7)}
        )
        self.run_test(text, exp_result=exp_result)

    def test_deduce_native_gates(self):
        """Test that the native gates are properly deduced from the text."""
        # Note: This behavior is possibly not what we want long term
        text = "register r[3]; foo 1 r[0]; bar 3.14"
        exp_native_gates = {
            'foo': self.get_gate_definition(
                'foo',
                [self.make_parameter(index=0, kind='float'),
                 self.make_parameter(index=1, kind='qubit')]
            ),
            'bar': self.get_gate_definition(
                'bar',
                [self.make_parameter(index=0, kind='float')]
            )

        }
        self.run_test(text, exp_native_gates=exp_native_gates)

    def test_use_native_gates(self):
        """Test that we can use the native gates in the QSCOUT native gate set."""
        text = "register r[3]; Rx r[0] 1.5"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            gates=[
                self.make_native_gate('Rx', ('r', 0), 1.5)
            ]
        )
        self.run_test(text, exp_result, use_qscout_native_gates=True)

    def test_fail_on_missing_native_gate(self):
        """Test that we fail when the using qscout native gates and the user uses a gate
        that does not exist."""
        text = "register r[3]; foo r[0] 1.5"
        # Make sure things we aren't doing something stupid and things will parse
        # without native gates on.
        parse_jaqal_string(text)
        with self.assertRaises(Exception):
            parse_jaqal_string(text, use_qscout_native_gates=True)

    def test_macro_definition_no_expand(self):
        """Test parsing macro definitions without expanding them."""
        text = "macro foo a { g a }; foo 1.5"
        exp_result = self.make_circuit(
            gates=[
                self.make_gate('foo', 1.5)
            ],
            macros={
                'foo': self.make_macro(
                    'foo',
                    ['a'],
                    self.make_gate('g', 'a')
                )
            }
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False)

    def test_macro_definition_expand(self):
        """Test parsing macro definitions and expanding them."""
        text = "macro foo a { g a }; foo 1.5"
        exp_result = self.make_circuit(
            gates=[
                self.make_gate('g', 1.5)
            ],
            # Even though we expand macros, we are not stripping the metadata,
            # so the definition will still be there.
            macros={
                'foo': self.make_macro(
                    'foo',
                    ['a'],
                    self.make_gate('g', 'a')
                )
            }
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False,
                      option=Option.expand_macro)

    def test_let_no_resolve(self):
        """Test parsing a let statement"""
        text = "let a 2; foo a"
        exp_result = self.make_circuit(
            gates=[
                self.make_gate('foo', self.make_constant('a', 2))
            ],
            constants={'a': self.make_constant('a', 2)}
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False,
                      option=Option.none)

    def test_let_resolve(self):
        """Test parsing a let statement and resolving it."""
        text = "let a 2; foo a"
        exp_result = self.make_circuit(
            gates=[
                self.make_gate('foo', 2)
            ],
            constants={'a': self.make_constant('a', 2)}
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False,
                      option=Option.expand_let)

    def test_map_no_resolve(self):
        """Test parsing a map statement."""
        text = "register r[3]; map q r[1:]; foo q[0]"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            maps={'q': self.make_map('q', 'r', (1, 3, 1))},
            gates=[
                self.make_gate('foo', ('q', 0))
            ]
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False,
                      option=Option.none)

    def test_map_single_qubit_no_resolve(self):
        text = "register r[3]; map q r[1]; foo q"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            maps={'q': self.make_map('q', 'r', 1)},
            gates=[
                self.make_gate('foo', self.make_named_qubit('q'))
            ]
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False,
                      option=Option.none)

    def test_map_resolve(self):
        """Test parsing a map statement and resolving it."""
        text = "register r[3]; map q r[1:]; foo q[0]"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            maps={'q': self.make_map('q', 'r', (1, 3, 1))},
            gates=[
                self.make_gate('foo', ('r', 1))
            ]
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False,
                      option=Option.expand_let_map)

    def test_map_single_qubit_resolve(self):
        text = "register r[3]; map q r[1]; foo q"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            maps={'q': self.make_map('q', 'r', 1)},
            gates=[
                self.make_gate('foo', ('r', 1))
            ]
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False,
                      option=Option.expand_let_map)

    def test_map_whole_register(self):
        text = "register r[3]; map q r; foo q[1]"
        exp_result = self.make_circuit(
            registers={'r': self.make_register('r', 3)},
            maps={'q': self.make_map('q', 'r', None)},
            gates=[self.make_gate('foo', ('q', 1))]
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False,
                      option=Option.none)

    def test_expand_macro_let_map_strip_metadata(self):
        """Test an example that exercises all available options."""
        text = "register r[3]; map q r; let a 2; macro foo x y { g x y }; foo q[a] 3.14"
        exp_result = self.make_circuit(
            registers={
                'r': self.make_register('r', 3)
            },
            constants={'a': self.make_constant('a', 2)},
            maps={'q': self.make_map('q', 'r', None)},
            macros={
                'foo': self.make_macro(
                    'foo',
                    ['x', 'y'],
                    self.make_gate('g', 'x', 'y')
                )
            },
            gates=[
                self.make_gate('g', ('r', 2), 3.14)
            ]
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False,
                      option=Option.full)

    def test_no_expand_macro_let_map_leave_metadata(self):
        """Test an example that does not exercise all available options but involves features that could be."""
        text = "register r[3]; map q r; let a 2; macro foo x y { g x y }; foo q[a] 3.14"
        exp_result = self.make_circuit(
            registers={
                'r': self.make_register('r', 3)
            },
            maps={'q': self.make_map('q', 'r', None)},
            constants={'a': self.make_constant('a', 2)},
            macros={
                'foo': self.make_macro(
                    'foo',
                    ['x', 'y'],
                    self.make_gate('g', 'x', 'y')
                )
            },
            gates=[
                self.make_gate('foo', ('q', self.make_constant('a', 2)), 3.14)
            ]
        )
        self.run_test(text, exp_result, use_qscout_native_gates=False,
                      option=Option.none)

    ##
    # Helper methods
    #

    def run_test(self, text, exp_result=None, exp_native_gates=None,
                 override_dict=None, use_qscout_native_gates=False, option=Option.none):
        act_result = parse_jaqal_string(text, override_dict=override_dict,
                                        use_qscout_native_gates=use_qscout_native_gates,
                                        processing_option=option)
        if exp_result is not None:
            self.assertEqual(exp_result.body, act_result.body)
            self.assertEqual(exp_result.macros, act_result.macros)
            self.assertEqual(exp_result.constants, act_result.constants)
            self.assertEqual(exp_result.registers, act_result.registers)
        if exp_native_gates is not None:
            self.assertEqual(exp_native_gates, act_result.native_gates)

    @staticmethod
    def make_circuit(*, gates, registers=None, macros=None, constants=None, maps=None):
        circuit = ScheduledCircuit()
        for gate in gates:
            circuit.body.append(gate)
        if registers:
            circuit.registers.update(registers)
        if macros:
            circuit.macros.update(macros)
        if constants:
            circuit.constants.update(constants)
        if maps:
            circuit.registers.update(maps)
        return circuit

    def make_gate(self, name, *args):
        """Return a GateStatement, possibly creating a definition in the process."""
        return self.make_gate_conditional(name, args, is_native=False)

    def make_native_gate(self, name, *args):
        """Return a GateStatement that must be a native gate."""
        return self.make_gate_conditional(name, args, is_native=True)

    def make_gate_conditional(self, name, args, is_native):
        """Make a gate that is either native or not. Don't call directly."""
        arg_objects = [self.make_argument_object(arg) for arg in args]
        if is_native:
            gate_def = self.get_native_gate_definition(name)
        else:
            params = [self.make_parameter_from_arg(idx, arg) for idx, arg in enumerate(args)]
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
    def get_native_gate_definition(name):
        """Return an existing GateDefinition for a native gate or raise an exception."""
        for gate in NATIVE_GATES:
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
        return Macro(name,
                     parameters=[self.make_parameter(pname) for pname in parameter_names],
                     body=self.make_sequential_gate_block(*statements))

    def make_constant(self, name, value):
        return Constant(name, value)

    def make_map(self, name, reg_name, reg_indexing):
        if reg_name not in self.registers:
            raise ValueError(f"Please create register {reg_name} first")
        if isinstance(reg_indexing, tuple):
            if len(reg_indexing) != 3:
                raise ValueError(f"reg_indexing must have 3 elements, found {len(reg_indexing)}")
            reg_indexing = tuple(self.make_slice_component(arg) for arg in reg_indexing)
            alias_slice = slice(*reg_indexing)
            reg = Register(name, alias_from=self.registers[reg_name],
                           alias_slice=alias_slice)
            self.registers[name] = reg
            return reg
        elif isinstance(reg_indexing, int):
            nq = NamedQubit(name, alias_from=self.registers[reg_name],
                            alias_index=reg_indexing)
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

class TestOption(TestCase):
    """Test the Option and OptionSet classes."""

    def test_contains_self(self):
        """Test that all options contain themselves."""
        for opt in Option:
            self.assertIn(opt, opt)

    def test_contains_bitmask(self):
        """Test that element containment acts like a bitmask."""
        for opt0 in Option:
            for opt1 in Option:
                self.assertEqual(opt0.value & opt1.value == opt1.value,
                                 opt1 in opt0)

    def test_in_option_set(self):
        """Test that options are in an option set containing them."""
        for opt0 in Option:
            for opt1 in Option:
                optset = opt0 | opt1
                self.assertIn(opt0, optset)
                self.assertIn(opt1, optset)

    def test_combine_opt_set_with_option(self):
        """Test that an option set combines with an option"""
        for opt0 in Option:
            for opt1 in Option:
                for opt2 in Option:
                    optset = opt0 | opt1
                    self.assertIn(opt2, optset | opt2)
                    self.assertIn(opt2, opt2 | optset)

    def test_let_in_optionset_with_let_map(self):
        """Test that extract_let is in an OptionSet that was created with extract_let_map but not extract_let"""
        optset = Option.expand_macro | Option.expand_let_map
        self.assertIn(Option.expand_let_map, optset)
