from unittest import TestCase

from jaqal.parser.interface import Interface, MemoizedInterface
from jaqal.parser.iter_gates import Gate, Loop, ParallelGateBlock, SequentialGateBlock
from jaqal.parser.identifier import Identifier


class InterfaceTester(TestCase):

    def test_single_gate(self):
        text = "register r[7]; foo r[0]"
        exp_result = [Gate('foo', [('r', 0)])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_single_loop(self):
        """Test returning a loop."""
        text = "loop 5 {foo}"
        exp_result = [Loop(5, SequentialGateBlock([Gate('foo', [])]))]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_loop_with_let_count(self):
        """Test a loop whose counter is set with a let statement."""
        text = "let n 10; loop n { foo }"
        exp_result = [Loop(10, SequentialGateBlock([Gate('foo', [])]))]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_nested_loop(self):
        """Test returning a loop within a loop."""
        text = "loop 5 { loop 2 { foo} }"
        exp_result = [Loop(5, SequentialGateBlock([
            Loop(2, SequentialGateBlock([Gate('foo', [])])),
        ]))]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_parallel_block(self):
        """Test returning a parallel block."""
        text = "< a | b | c >"
        exp_result = [ParallelGateBlock([Gate('a', []), Gate('b', []), Gate('c', [])])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_sequential_block(self):
        """Test that a sequential block is removed at the top level."""
        text = "{ a ; b ; c }"
        exp_result = [Gate('a', []), Gate('b', []), Gate('c', [])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_nested_blocks(self):
        """Test that parallel and sequential blocks nested within each other are normalized."""
        text = '{g0;g1;<p0|p1|p2|{q0;q1}>;g2}'
        exp_result = [
            Gate('g0', []),
            Gate('g1', []),
            ParallelGateBlock([
                Gate('p0', []),
                Gate('p1', []),
                Gate('p2', []),
                Gate('q0', []),
            ]),
            Gate('q1', []),
            Gate('g2', []),
        ]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_simple_map(self):
        """Test remapping the entire qubit register."""
        text = "register r[7]; map a r; foo a[1]"
        exp_result = [Gate('foo', [('r', 1)])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_map_slice(self):
        """Test remapping a register with a slice."""
        text = "register r[7]; map a r[1:7:2]; foo a[1]"
        exp_result = [Gate('foo', [('r', 3)])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_map_element(self):
        """Test remapping a single register element."""
        text = "register r[7]; map a r[1]; foo a"
        exp_result = [Gate('foo', [('r', 1)])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_map_with_let(self):
        """Test a map that uses a let value to determine which index is chosen."""
        text = "register r[7]; let x 1; map a r[x]; foo a"
        exp_result = [Gate('foo', [('r', 1)])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_map_with_let_override(self):
        """Test a map that uses a let value to determine which index is chosen."""
        text = "register r[7]; let x 1; map a r[x]; foo a"
        exp_result = [Gate('foo', [('r', 4)])]
        let_dict = {'x': 4}
        self.run_test(text, let_dict, exp_result)

    def test_nested_map_with_let(self):
        """Test multiple map statements that chain and use let statements to choose which qubit to access."""
        text = "register r[7]; let x 1; let y 2; map b r[x:]; map a b[::y]; foo a[1]"
        exp_result = [Gate('foo', [('r', 3)])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_let_override(self):
        """Test overriding a let value with a dictionary."""
        text = "let x 1; foo x"
        exp_result = [Gate('foo', [2])]
        let_dict = {'x': 2}
        self.run_test(text, let_dict, exp_result)

    def test_expand_macro(self):
        """Test expanding a macro."""
        text = "macro foo a { g a; h 5 }; foo 1"
        exp_result = [Gate('g', [1]), Gate('h', [5])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_nested_macros(self):
        """Test expanding a macro nested within another macro."""
        text = "macro foo { g }; macro bar { foo }; bar"
        exp_result = [Gate('g', [])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_macro_argument_shadowing_let(self):
        """Test that a macro argument takes precedence when named the same as a let constant."""
        text = "let a 15; macro foo a { g a; h 5 }; foo 1"
        exp_result = [Gate('g', [1]), Gate('h', [5])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_macro_argument_shadowing_map(self):
        """Test that a macro argument takes precedence when named the same as a map alias."""
        text = "register r[7]; map a r[1]; macro foo a { g a; h 5 }; foo 1"
        exp_result = [Gate('g', [1]), Gate('h', [5])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_let_substitution_in_macro(self):
        """Test that let values are substituted into the body of a macro."""
        text = "let a 1; macro foo { g a; h 5 }; foo"
        exp_result = [Gate('g', [1]), Gate('h', [5])]
        let_dict = {}
        self.run_test(text, let_dict, exp_result)

    def test_export_register(self):
        """Test that a register is exported with its size."""
        text = "register r[7]"
        exp_result = {'r': 7}
        iface = Interface(text, allow_no_usepulses=True)
        _, act_result = iface.get_uniformly_timed_gates_and_registers({})
        self.assertEqual(exp_result, act_result)

    def test_export_register_with_let(self):
        """Test that a register with a size set by a let statement is properly exported."""
        text = "let a 7; register r[a]"
        exp_result = {'r': 7}
        iface = Interface(text, allow_no_usepulses=True)
        _, act_result = iface.get_uniformly_timed_gates_and_registers({})
        self.assertEqual(exp_result, act_result)

    def test_usepulses(self):
        """Test getting information from the usepulses statement."""
        text = "from foo.bar usepulses *"
        exp_result = {Identifier.parse('foo.bar'): all}
        iface = Interface(text, allow_no_usepulses=True)
        act_result = iface.usepulses
        self.assertEqual(exp_result, act_result)

    def test_memoize(self):
        """Test that a memoized interface saves its entries."""
        text = "let a 7; register r[10]; foo r[a]"
        iface = MemoizedInterface(text, allow_no_usepulses=True)
        let_dict = {'a': 2}
        exp_result = [Gate('foo', [('r', 2)])]
        act_result, _ = iface.get_uniformly_timed_gates_and_registers(let_dict)
        self.assertEqual(exp_result, act_result)
        iface._initial_tree = None  # This uses guilty knowledge to break the invariants
        with self.assertRaises(Exception):
            iface.get_uniformly_timed_gates_and_registers({'a': 11})
        # But since the result is cached, this computation should still work
        act_result, _ = iface.get_uniformly_timed_gates_and_registers(let_dict)
        self.assertEqual(exp_result, act_result)

    def test_memoize_key_order_independence(self):
        """Test that a memoized interface is independent of its key ordering."""
        text = "let a 7; let b 5; register r[10]; foo r[a]; bar r[b]"
        iface = MemoizedInterface(text, allow_no_usepulses=True)
        let_dict = {'a': 2, 'b': 3}
        exp_result = [Gate('foo', [('r', 2)]), Gate('bar', [('r', 3)])]
        act_result, _ = iface.get_uniformly_timed_gates_and_registers(let_dict)
        self.assertEqual(exp_result, act_result)
        iface._initial_tree = None  # Break things
        tel_dict = {'b': 3, 'a': 2}
        act_result, _ = iface.get_uniformly_timed_gates_and_registers(tel_dict)
        self.assertEqual(exp_result, act_result)

    ##
    # Rejection tests
    #

    def test_reject_unknown_register(self):
        """Test that we raise an exception if a gate uses an unknown register."""
        text = "register r[7]; foo q[0]"
        let_dict = {}
        self.run_reject(text, let_dict)

    def test_reject_bad_register_index(self):
        """Test that we raise an exception when accessing an element beyond a register's end."""
        text = "register r[7]; foo r[7]"
        let_dict = {}
        self.run_reject(text, let_dict)

    def test_reject_bad_register_mapped(self):
        """Test that we raise an exception when accessing an element beyond a register's end that has been slightly
        obfuscated with let and map statements."""
        text = "register r[7]; let x 3; map a r[x:]; foo a[4]"
        let_dict = {}
        self.run_reject(text, let_dict)

    def test_reject_bad_let_override(self):
        """Test rejecting attempting to override a let statement with an unknown variable."""
        text = "register r[7]; let a 3; foo r[a]"
        let_dict = {'b': 2}
        self.run_reject(text, let_dict)

    def test_reject_floating_point_let_as_index(self):
        """Test that we reject a let value that is a floating point used as an index."""
        text = "register r[7]; let a 3.14; foo r[a]"
        let_dict = {}
        self.run_reject(text, let_dict)

    def test_reject_loop_in_block(self):
        """Test that we reject a loop inside of a (non-macro, non-loop) block."""
        # Note: Although I think I had a good reason, I can't remember why we're rejecting these.
        text = "<loop 5 { foo }>"
        let_dict = {}
        self.run_reject(text, let_dict)
        text = "<{loop 5 { foo }}>"
        self.run_reject(text, let_dict)

    def test_reject_non_integer_register_size_with_let(self):
        """Test that we reject setting the register size to a real with a let."""
        text = "let a 3.14; register r[a]"
        let_dict = {}
        self.run_reject(text, let_dict)

    def test_reject_multiple_usepulses(self):
        """Test that we reject multiple usepulses statements. This is temporary."""
        text = "from foo usepulses *; from bar usepulses *"
        let_dict = {}
        self.run_reject(text, let_dict)

    def test_reject_no_usepulses(self):
        """Test that with allow_no_usepulses=False, the interface rejects Jaqal without usepulses."""
        text = "gate 0 1 2 3"
        with self.assertRaises(Exception):
            Interface(text)

    ##
    # Running tests
    #

    def run_test(self, text, let_dict, exp_result):
        iface = Interface(text, allow_no_usepulses=True)
        act_result, _ = iface.get_uniformly_timed_gates_and_registers(let_dict)
        self.assertEqual(exp_result, act_result)

    def run_reject(self, text, let_dict):
        with self.assertRaises(Exception):
            iface = Interface(text, allow_no_usepulses=True)
            iface.get_uniformly_timed_gates_and_registers(let_dict)
