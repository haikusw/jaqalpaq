import unittest, pytest
from pathlib import Path
from jaqalpaq.parser import parse_jaqal_file
from jaqalpaq.core.circuitbuilder import build

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
        pytest.importorskip("qscout")
        with open(sexp_filename, "r") as fd:
            sexp = eval(fd.read())
        act_circuit = parse_jaqal_file(jaqal_filename, autoload_pulses=False)
        exp_circuit = build(sexp)
        self.assertEqual(exp_circuit, act_circuit)

    def test_hadamard(self):
        """Test Hadamard example"""
        jaqal_filename = example_dir / "bell_prep.jaqal"
        sexp_filename = example_dir / "bell_prep.py"
        self.implement_file_test(jaqal_filename, sexp_filename)

    def test_gst(self):
        """Test Single Qubit GST example"""
        jaqal_filename = example_dir / "single_qubit_gst.jaqal"
        sexp_filename = example_dir / "single_qubit_gst.py"
        self.implement_file_test(jaqal_filename, sexp_filename)
