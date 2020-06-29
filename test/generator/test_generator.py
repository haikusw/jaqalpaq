from unittest import TestCase

from jaqalpaq.generator import generate_jaqal_program
from jaqalpaq.parser import parse_jaqal_string


class GeneratorTester(TestCase):
    def run_test(self, program):
        with open(program) as fd:
            self.run_test_string(fd.read())

    def run_test_string(self, text):
        circuit1 = parse_jaqal_string(text, autoload_pulses=False)
        generated = generate_jaqal_program(circuit1)
        circuit2 = parse_jaqal_string(generated, autoload_pulses=False)
        self.assertEqual(circuit1, circuit2)

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
        self.run_test("examples/jaqal/hadamard.jaqal")

    def test_single_qubit_gs(self):
        self.run_test("examples/jaqal/single_qubit_gst.jaqal")

    def test_randomized_rotations(self):
        from random import uniform
        from math import pi
        from tempfile import TemporaryDirectory
        import os.path

        with TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, "randomness_example.jql"), "w") as f:
                f.write("register q[1]\n\n")
                for idx in range(100):
                    angle = uniform(0.0, 2.0) * pi
                    f.write("prepare_all\n")
                    f.write("Rx q[0] %f\n" % angle)
                    f.write("measure_all\n\n")
            self.run_test(os.path.join(tempdir, "randomness_example.jql"))

    def test_let_in_register(self):
        self.run_test_string("let len 3; register q[len]")
