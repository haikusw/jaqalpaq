import unittest
from pathlib import Path
from jaqal.jaqal.parser import parse_jaqal_file
from jaqal.core.circuitbuilder import build

top_example_dir = Path("examples/jaqal")
test_example_dir = Path("../examples/jaqal")

if top_example_dir.exists():
    example_dir = top_example_dir
elif test_example_dir.exists():
    example_dir = test_example_dir
else:
    raise IOError("Cannot find example directory")


class ExampleFileTester(unittest.TestCase):
    def implement_file_test(self, jaqal_filename, sexp_filename):
        with open(sexp_filename, "r") as fd:
            sexp = eval(fd.read())
        act_circuit = parse_jaqal_file(jaqal_filename)
        exp_circuit = build(sexp)
        self.assertEqual(exp_circuit, act_circuit)

    def test_hadamard(self):
        """Test Hadamard example"""
        jaqal_filename = example_dir / "hadamard.jaqal"
        sexp_filename = example_dir / "hadamard.py"
        self.implement_file_test(jaqal_filename, sexp_filename)

    def test_gst(self):
        """Test Single Qubit GST example"""
        jaqal_filename = example_dir / "single_qubit_gst.jaqal"
        sexp_filename = example_dir / "single_qubit_gst.py"
        self.implement_file_test(jaqal_filename, sexp_filename)
