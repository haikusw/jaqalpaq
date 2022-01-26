import unittest

from jaqalpaq.core.circuitbuilder import build, Builder, SExpression
from jaqalpaq.core import (
    Parameter,
    Register,
    NamedQubit,
    Constant,
    GateDefinition,
    ParamType,
)
import jaqalpaq.core as core
from jaqalpaq.error import JaqalError

from . import randomize
from . import common


class BuildTester(unittest.TestCase):
    def test_pass_through_core_type(self):
        test_values = [
            Parameter("foo", None),
            Register("r", 3),
        ]
        for value in test_values:
            self.assertEqual(value, build(value))

    def test_build_integer(self):
        exp_value = randomize.random_integer()
        act_value = build(exp_value)
        self.assertEqual(exp_value, act_value)

    def test_build_float(self):
        exp_value = randomize.random_float()
        act_value = build(exp_value)
        common.assert_values_same(self, exp_value, act_value)

    def test_build_register(self):
        name = randomize.random_identifier()
        size = randomize.random_whole()
        sexpr = ("register", name, size)
        exp_value = Register(name, size)
        act_value = build(sexpr)
        self.assertEqual(exp_value, act_value)

    def test_build_map_full(self):
        # This requires a defined register to test so this requires a circuit.
        rname = randomize.random_identifier()
        rsize = randomize.random_whole()
        mname = randomize.random_identifier()
        sexpr = ("circuit", ("register", rname, rsize), ("map", mname, rname))
        reg = Register(rname, rsize)
        exp_value = Register(mname, alias_from=reg)
        circuit = build(sexpr)
        act_value = circuit.registers[mname]
        self.assertEqual(exp_value, act_value)

    def test_build_map_single(self):
        rname = randomize.random_identifier()
        rsize = randomize.random_whole()
        mname = randomize.random_identifier()
        mindex = randomize.random_integer(lower=0, upper=rsize - 1)
        reg = Register(rname, rsize)
        exp_value = NamedQubit(mname, reg, mindex)
        sexpr = ("circuit", ("register", rname, rsize), ("map", mname, rname, mindex))
        circuit = build(sexpr)
        act_value = circuit.registers[mname]
        self.assertEqual(exp_value, act_value)

    def test_build_map_slice(self):
        rname = randomize.random_identifier()
        rsize = randomize.random_whole()
        mname = randomize.random_identifier()
        mstart = randomize.random_integer(lower=0, upper=rsize - 1)
        mstop = randomize.random_integer(lower=1, upper=rsize)
        mstep = randomize.random_integer(lower=1, upper=rsize)
        # The Register type doesn't seem to work with None (default) slice parameters, so we don't test that here.
        # it's not clear if that's something to worry about.
        mslice = slice(mstart, mstop, mstep)
        reg = Register(rname, rsize)
        exp_value = Register(mname, alias_from=reg, alias_slice=mslice)
        sexpr = (
            "circuit",
            ("register", rname, rsize),
            ("map", mname, rname, mstart, mstop, mstep),
        )
        circuit = build(sexpr)
        act_value = circuit.registers[mname]
        self.assertEqual(exp_value, act_value)

    def test_build_let(self):
        name = randomize.random_identifier()
        value = randomize.random_integer()
        sexpr = ("let", name, value)
        exp_value = Constant(name, value)
        act_value = build(sexpr)
        self.assertEqual(exp_value, act_value)

    def test_build_macro_definition(self):
        gate_def = GateDefinition("foo", parameters=[Parameter("x", None)])
        sexpr = (
            "macro",
            "bar",
            "a",
            "b",
            ("sequential_block", ("gate", "foo", "a"), ("gate", "foo", "b")),
        )
        act_value = build(sexpr, inject_pulses={"foo": gate_def})
        exp_value = core.Macro(
            "bar", parameters=[Parameter("a", None), Parameter("b", None)]
        )
        exp_value.body.statements.append(
            core.GateStatement(gate_def, parameters={"x": Parameter("a", None)})
        )
        exp_value.body.statements.append(
            core.GateStatement(gate_def, parameters={"x": Parameter("b", None)})
        )
        self.assertEqual(exp_value, act_value)

    def test_build_macro_with_premade_parameters(self):
        param_ident = randomize.random_identifier()
        param = Parameter(param_ident, None)
        macro_ident = randomize.random_identifier()
        sexpr = ("macro", macro_ident, param, ("sequential_block",))
        exp_value = core.Macro(macro_ident, [param])
        act_value = build(sexpr)
        self.assertEqual(exp_value, act_value)

    def test_build_anonymous_gate(self):
        # To test this we're going to create a gate, then take the temporary definition that is created in the process,
        # and use that to create an identical gate.
        name = randomize.random_identifier()
        args = (1, 3.14)
        sexpr = ("gate", name, *args)
        act_value = build(sexpr)
        gate_def = act_value.gate_def
        exp_value = gate_def(*args)
        self.assertEqual(exp_value, act_value)

    def test_build_native_gate(self):
        name = randomize.random_identifier()
        parameters = [Parameter("a", ParamType.INT), Parameter("b", ParamType.FLOAT)]
        gate_def = GateDefinition(name, parameters=parameters)
        native_gates = {name: gate_def}
        a = 5
        b = 1.234
        sexpr = ("gate", name, a, b)
        exp_value = gate_def(a, b)
        act_value = build(sexpr, native_gates)
        self.assertEqual(exp_value, act_value)

    def test_build_usepulses(self):
        sexpr0 = ("usepulses", "__invalid__module__test0", all)
        sexpr1 = ("usepulses", "__invalid__module__test1", "*")
        up0 = build(sexpr0)
        up1 = build(sexpr1)
        self.assertNotEqual(up0, up1)

        self.assertEqual(up0.names, all)
        self.assertEqual(up1.names, all)
        self.assertEqual(up0.module, "__invalid__module__test0")
        self.assertEqual(up1.module, "__invalid__module__test1")

    def test_fail_anonymous_gate(self):
        """Test that we fail when using an anonymous gate if we only allow native gates."""
        sexpr = ("gate", "foo")
        with self.assertRaises(JaqalError):
            build(sexpr, {})

    def test_fail_redefine_gate(self):
        sexpr = (
            "circuit",
            ("gate", "foo"),
            ("macro", "foo", ("sequential_block", ("gate", "bar"))),
            ("gate", "foo"),
        )
        with self.assertRaises(JaqalError):
            build(sexpr, {})

    def test_unhashable_gate(self):
        """Test making a gate with lists instead of tuples. This has in the
        past not worked well with the gate memoizer."""
        sexpr = [
            "circuit",
            ["register", "r", 3],
            ["gate", "foo", ["array_item", "r", 0]],
        ]
        exp_value = build(
            ("circuit", ("register", "r", 3), ("gate", "foo", ("array_item", "r", 0)))
        )
        act_value = build(sexpr)
        # The most likely failure case is not this assertion but
        # rather that we would throw an exception while building the
        # sexpr in the first place.
        self.assertEqual(exp_value, act_value)

    def test_build_macro_gate(self):
        sexpr = ("circuit", ("macro", "foo", ("sequential_block",)), ("gate", "foo"))
        circuit = build(sexpr, {})
        # The fact that this didn't raise an exception is mostly what we're testing.
        macro = circuit.macros["foo"]
        act_value = circuit.body.statements[0]
        exp_value = macro()
        self.assertEqual(exp_value, act_value)

    def test_build_sequential_block(self):
        sexpr = ("sequential_block", ("gate", "foo"), ("gate", "bar", 123))
        block: core.BlockStatement = build(sexpr)
        self.assertEqual(2, len(block))
        self.assertFalse(block.parallel)
        self.assertEqual(block.statements[0].name, "foo")
        self.assertEqual(block.statements[1].name, "bar")
        self.assertEqual(block.statements[1].parameters["p0"], 123)

    def test_build_parallel_block(self):
        sexpr = ("parallel_block", ("gate", "foo"), ("gate", "bar", 123))
        block: core.BlockStatement = build(sexpr)
        self.assertEqual(2, len(block))
        self.assertTrue(block.parallel)
        self.assertEqual(block.statements[0].name, "foo")
        self.assertEqual(block.statements[1].name, "bar")
        self.assertEqual(block.statements[1].parameters["p0"], 123)

    def test_build_subcircuit(self):
        sexpr = ("subcircuit_block", 100, ("gate", "foo"))
        block: core.BlockStatement = build(sexpr)
        self.assertEqual(1, len(block))
        self.assertFalse(block.parallel)
        self.assertEqual(block.iterations, 100)
        self.assertTrue(block.subcircuit)
        self.assertEqual(block.statements[0].name, "foo")

    def test_build_loop(self):
        count = randomize.random_whole()
        sexpr = ("loop", count, ("sequential_block", ("gate", "foo")))
        loop: core.LoopStatement = build(sexpr)
        self.assertEqual(count, loop.iterations)
        self.assertEqual(1, len(loop.statements))
        self.assertEqual(loop.statements[0].name, "foo")

    def test_build_qubit_gate_argument(self):
        sexpr = (
            "circuit",
            ("register", "r", 3),
            ("gate", "foo", ("array_item", "r", 0)),
        )
        circuit: core.Circuit = build(sexpr)
        exp_value = circuit.registers["r"][0]
        act_value = circuit.body.statements[0].parameters["p0"]
        self.assertEqual(exp_value, act_value)

    def test_build_map_with_let(self):
        sexpr = (
            "circuit",
            ("let", "a", 1),
            ("register", "r", 10),
            ("map", "q", "r", "a"),
        )
        reg = Register("r", 10)
        const = Constant("a", 1)
        exp_value = NamedQubit("q", reg, const)
        circuit = build(sexpr)
        act_value = circuit.registers["q"]
        self.assertEqual(exp_value, act_value)

    def test_build_map_slice_with_let(self):
        sexpr = (
            "circuit",
            ("let", "a", 0),
            ("let", "b", 3),
            ("let", "c", 2),
            ("register", "r", 3),
            ("map", "q", "r", "a", "b", "c"),
        )
        reg = Register("r", 3)
        const_a = Constant("a", 0)
        const_b = Constant("b", 3)
        const_c = Constant("c", 2)
        exp_value = Register(
            "q", alias_from=reg, alias_slice=slice(const_a, const_b, const_c)
        )
        circuit = build(sexpr)
        act_value = circuit.registers["q"]
        self.assertEqual(exp_value, act_value)

    def test_build_gate_with_constant(self):
        gate_def = GateDefinition("g", [Parameter("p", None)])
        sexpr = ("circuit", ("let", "a", 1), ("gate", "g", "a"))
        exp_value = gate_def(Constant("a", 1))
        circuit = build(sexpr, inject_pulses={"g": gate_def})
        act_value = circuit.body.statements[0]
        self.assertEqual(exp_value, act_value)

    def test_build_gate_memo(self):
        """Test that two identical gates in different contexts do not build to
        the same gate."""
        # This uses a non-public class because it's the most direct
        # way to test what we're getting at.
        builder = Builder(inject_pulses=None, autoload_pulses=False, filename=None)
        sexpr = SExpression.create(["gate", "foo", "a"])
        gate_context = {}
        context0 = {"a": Constant("a", 0)}
        context1 = {"a": Constant("a", 1)}
        gate0 = builder.build_gate(sexpr, context0, gate_context)
        same_gate0 = builder.build_gate(sexpr, context0, gate_context)
        self.assertIs(gate0, same_gate0)
        gate1 = builder.build_gate(sexpr, context1, gate_context)
        self.assertNotEqual(gate0, gate1)

    def test_unnormalized_native_gates(self):
        """Test using native gates that are not a dictionary."""
        gate_def = GateDefinition("g", [Parameter("p", None)])
        sexpr = ("circuit", ("gate", "g", 0))
        exp_value = gate_def(0)
        circuit = build(sexpr, inject_pulses=[gate_def])
        act_value = circuit.body.statements[0]
        self.assertEqual(exp_value, act_value)

    def test_build_circuit(self):
        """Build a circuit with as many features as possible."""
        # We've already built a circuit elsewhere but this test tries to tie everything in together.
        gate_def = GateDefinition("g", [Parameter("p", None)])
        native_gates = {"g": gate_def}
        sexpr = (
            "circuit",
            ("register", "r", 7),
            ("map", "q", "r"),
            ("let", "x", 0),
            ("macro", "foo", "a", ("sequential_block", ("gate", "g", "a"))),
            ("gate", "foo", "x"),
            ("loop", 5, ("sequential_block", ("gate", "g", 3))),
            ("parallel_block", ("gate", "g", 0), ("gate", "g", 1)),
        )
        act_value = build(sexpr, inject_pulses=native_gates)

        r = Register("r", 7)
        q = Register("q", alias_from=r)
        x = Constant("x", 0)
        foo = core.Macro("foo", parameters=[Parameter("a", None)])
        foo.body.statements.append(gate_def(Parameter("a", None)))
        exp_value = core.Circuit(native_gates=native_gates)
        exp_value.registers[r.name] = r
        exp_value.registers[q.name] = q
        exp_value.constants[x.name] = x
        exp_value.macros[foo.name] = foo
        exp_value.body.statements.append(foo(x))
        loop_block = core.BlockStatement(statements=[gate_def(3)])
        loop = core.LoopStatement(5, loop_block)
        exp_value.body.statements.append(loop)
        parallel_block = core.BlockStatement(parallel=True)
        parallel_block.statements.append(gate_def(0))
        parallel_block.statements.append(gate_def(1))
        exp_value.body.statements.append(parallel_block)

        self.assertEqual(exp_value, act_value)


class ObjectOrientedBuilderTester(unittest.TestCase):
    """Test the object-oriented tester. Evaluate all things immediately where the option exists."""

    def test_add_gate_to_block(self):
        """Test adding a gate to a sequential block."""
        builder = core.circuitbuilder.SequentialBlockBuilder()
        builder.gate("foo", 3.14, 1)
        self.run_test(("sequential_block", ("gate", "foo", 3.14, 1)), builder)

    def test_add_sequential_block_to_block(self):
        builder = core.circuitbuilder.SequentialBlockBuilder()
        block = builder.block()
        block.gate("foo")
        self.run_test(
            ("sequential_block", ("sequential_block", ("gate", "foo"))), builder
        )

    def test_add_loop_to_block(self):
        iterations = 5
        builder = core.circuitbuilder.SequentialBlockBuilder()
        loop_block_builder = core.circuitbuilder.SequentialBlockBuilder()
        loop_block_builder.gate("foo")
        loop_block_builder.gate("bar")
        builder.loop(iterations, loop_block_builder)
        self.run_test(
            (
                "sequential_block",
                (
                    "loop",
                    iterations,
                    ("sequential_block", ("gate", "foo"), ("gate", "bar")),
                ),
            ),
            builder,
        )

    def test_add_parallel_block_to_block(self):
        builder = core.circuitbuilder.SequentialBlockBuilder()
        block = builder.block(parallel=True)
        block.gate("foo")
        block.gate("bar")
        self.run_test(
            ("sequential_block", ("parallel_block", ("gate", "foo"), ("gate", "bar"))),
            builder,
        )

    def test_add_usepulses_to_circuit(self):
        builder = core.circuitbuilder.CircuitBuilder()
        builder.usepulses("abc.xyz", all)
        self.run_test(("circuit", ("usepulses", "abc.xyz", all)), builder)

    def test_add_register_to_circuit(self):
        builder = core.circuitbuilder.CircuitBuilder()
        builder.register("r", 3)
        self.run_test(("circuit", ("register", "r", 3)), builder)

    def test_add_let_to_circuit(self):
        builder = core.circuitbuilder.CircuitBuilder()
        builder.let("x", -1)
        self.run_test(("circuit", ("let", "x", -1)), builder)

    def test_add_macro_to_circuit(self):
        foo_def = core.GateDefinition("foo", parameters=[Parameter("x", None)])
        native_gates = {"foo": foo_def}
        block = core.circuitbuilder.SequentialBlockBuilder()
        block.gate("foo", "a")
        builder = core.circuitbuilder.CircuitBuilder(native_gates=native_gates)
        builder.macro("my_macro", ["a"], body=block)
        self.run_test(
            (
                "circuit",
                ("macro", "my_macro", "a", ("sequential_block", ("gate", "foo", "a"))),
            ),
            builder,
            native_gates=native_gates,
        )

    def test_use_qubit_in_gate(self):
        foo_def = core.GateDefinition("foo", [core.Parameter("p0", ParamType.QUBIT)])
        native_gates = {"foo": foo_def}
        builder = core.circuitbuilder.CircuitBuilder(native_gates=native_gates)
        reg = builder.register("r", 3)
        builder.gate("foo", reg[0])
        self.run_test(
            ("circuit", ("register", "r", 3), ("gate", "foo", ("array_item", "r", 0))),
            builder,
            native_gates=native_gates,
        )

    def test_use_constant_in_gate(self):
        foo_def = core.GateDefinition("foo", [core.Parameter("p0", None)])
        native_gates = {"foo": foo_def}
        builder = core.circuitbuilder.CircuitBuilder(native_gates=native_gates)
        const = builder.let("x", 1)
        builder.gate("foo", const)
        self.run_test(
            ("circuit", ("let", "x", 1), ("gate", "foo", "x")),
            builder,
            native_gates=native_gates,
        )

    def test_use_constant_in_register(self):
        builder = core.circuitbuilder.CircuitBuilder()
        size = builder.let("size", 3)
        builder.register("r", size)
        self.run_test(
            ("circuit", ("let", "size", 3), ("register", "r", "size")), builder
        )

    def test_use_macro_gate(self):
        g_def = core.GateDefinition("g", [Parameter("p0", None)])
        native_gates = {"g": g_def}
        builder = core.circuitbuilder.CircuitBuilder(native_gates=native_gates)
        block = core.circuitbuilder.SequentialBlockBuilder()
        block.gate("g", "a")
        builder.macro("foo", ["a"], block)
        builder.gate("foo", 1)
        self.run_test(
            (
                "circuit",
                ("macro", "foo", "a", ("sequential_block", ("gate", "g", "a"))),
                ("gate", "foo", 1),
            ),
            builder,
            native_gates=native_gates,
        )

    def test_stretch_register(self):
        builder = core.circuitbuilder.CircuitBuilder()
        builder.register("r", 3)
        self.assertTrue(builder.stretch_register(3))
        self.assertTrue(builder.stretch_register(6))
        self.assertFalse(builder.stretch_register(2))
        self.run_test(("circuit", ("register", "r", 6)), builder)

    def test_map_register(self):
        builder = core.circuitbuilder.CircuitBuilder()
        r = builder.register("r", 3)
        builder.map("alias", r)
        builder.map("named", r, 0)
        builder.map("sliced", r, slice(0, 2))
        self.run_test(
            (
                "circuit",
                ("register", "r", 3),
                ("map", "alias", "r"),
                ("map", "named", "r", 0),
                ("map", "sliced", "r", 0, 2, 1),
            ),
            builder,
        )

    def test_nested_macros(self):
        """Test that parameters are properly expanded in nested scopes."""
        gate_def = GateDefinition("g", [Parameter("p", ParamType.QUBIT)])
        native_gates = {"g": gate_def}
        builder = core.circuitbuilder.CircuitBuilder(native_gates=native_gates)

        (q,) = builder.register("r", 1)

        inner_builder = core.circuitbuilder.SequentialBlockBuilder()
        inner_builder.gate("g", "c")
        builder.macro("inner", ["c"], inner_builder)

        outer_builder = core.circuitbuilder.SequentialBlockBuilder()
        outer_builder.gate("inner", "ctrl1")
        builder.macro("outer", ["ctrl1"], outer_builder)

        builder.gate("outer", q)

        circuit = builder.build()
        macro_inner = circuit.macros["inner"]
        macro_outer = circuit.macros["outer"]

        self.assertEqual(macro_inner, macro_outer.body.statements[0]._gate_def)

    ##
    # Helper methods
    #

    def run_test(self, exp_sexpr, act_builder, native_gates=None):
        """Run the test by evaluating the results of using the given s-expression vs. using the given builder."""
        exp_value = build(exp_sexpr, inject_pulses=native_gates)
        act_value = act_builder.build()
        self.assertEqual(exp_value, act_value)
