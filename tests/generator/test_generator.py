from re import sub, DOTALL
from unittest import TestCase

from jaqalpaq.generator import generate_jaqal_program
from jaqalpaq.parser import parse_jaqal_string


class GeneratorTester(TestCase):
    def run_test(self, program):
        with open(program) as fd:
            self.run_test_string(fd.read())

    def normalize_jaqal(self, text):
        # replace tabs
        text = sub("\t", " ", text)

        # remove comments
        text = sub("//.*", "", text)
        text = sub(r"/\*.*\*/", "", text, flags=DOTALL)

        # expand parallel blocks
        text = sub(r"\|", "\n", text)
        text = sub("<", "\n<\n", text)
        text = sub(">", "\n>\n", text)

        # expand serial blocks
        text = sub(";", "\n", text)
        text = sub("{", "\n{\n", text)
        text = sub("}", "\n}\n", text)

        # drop zeros at the ends of numbers
        text = sub("(?<=[0123456789])0+(?= |\n)", "\n", text)

        # ignore register statements (ambiguous order in header)
        text = sub("(^|\n) *register .*(\n|$)", "\n", text)

        # remove repeated whitespace
        text = sub(" +", " ", text)
        text = sub(" *\n *", "\n", text)
        text = sub("\n+", "\n", text)
        text = sub("^( |\n)*", "", text)
        text = sub("( |\n)*$", "", text)

        return text

    def run_test_string(self, text):
        circuit1 = parse_jaqal_string(text, autoload_pulses=False)
        generated = generate_jaqal_program(circuit1)
        circuit2 = parse_jaqal_string(generated, autoload_pulses=False)
        self.assertEqual(circuit1, circuit2)
        self.assertEqual(self.normalize_jaqal(text), self.normalize_jaqal(generated))

    def test_map_registers(self):
        self.run_test("examples/jaqal/spec_samples/registers.jaqal")

    def test_bell_preparation(self):
        self.run_test("examples/jaqal/spec_samples/bell.jaqal")

    def test_block_statements(self):
        self.run_test("examples/jaqal/spec_samples/blocks.jaqal")

    def test_precomputed_constants(self):
        self.run_test("examples/jaqal/spec_samples/compile.jaqal")

    def test_define_constants(self):
        self.run_test("examples/jaqal/spec_samples/constants.jaqal")

    def test_controlled_rz(self):
        self.run_test("examples/jaqal/spec_samples/crz.jaqal")

    def test_loop_statements(self):
        self.run_test("examples/jaqal/spec_samples/loop.jaqal")

    def test_define_macro(self):
        self.run_test("examples/jaqal/spec_samples/macro.jaqal")

    def test_output_example(self):
        self.run_test("examples/jaqal/spec_samples/output.jaqal")

    def test_slice_registers(self):
        self.run_test("examples/jaqal/spec_samples/slice.jaqal")

    def test_sxx_gate(self):
        self.run_test("examples/jaqal/spec_samples/two_qubit_gate.jaqal")

    def test_hadamard_macro(self):
        self.run_test("examples/jaqal/bell_prep.jaqal")

    def test_single_qubit_gs(self):
        self.run_test("examples/jaqal/single_qubit_gst.jaqal")

    def test_randomized_rotations(self):
        from random import uniform
        from math import pi

        lines = []
        lines.append("register q[1]\n")
        for idx in range(100):
            angle = uniform(0.0, 2.0) * pi
            lines.append("prepare_all")
            lines.append("Rx q[0] %f" % angle)
            lines.append("measure_all\n")
        self.run_test_string("\n".join(lines))

    def test_let_in_register(self):
        self.run_test_string("let len 3; register q[len]")

    def test_let_in_register_qubit(self):
        self.run_test_string("let i 1; register q[2]; Rx q[i] 1")
