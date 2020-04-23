import unittest
from pathlib import Path
from .helpers.parser import ParserTesterMixin
from jaqal.parser.parse import make_lark_parser

from jaqal.parser.interface import Interface

top_example_dir = Path('examples/jaqal')
test_example_dir = Path('../examples/jaqal')

if top_example_dir.exists():
    example_dir = top_example_dir
elif test_example_dir.exists():
    example_dir = test_example_dir
else:
    raise IOError('Cannot find example directory')


class ExampleFileTester(ParserTesterMixin, unittest.TestCase):

    def implement_file_test(self, file_name):
        text = Path(file_name).read_text()
        parser = make_lark_parser()
        try:
            tree = parser.parse(text)
        except Exception as e: 
            raise AssertionError(f"{file_name}: {e}")
        return tree

    def test_hadamard(self):
        """Test Hadamard example"""
        self.implement_file_test(example_dir / "hadamard.jaqal")
 
    def test_gst(self):
        """Test Single Qubit GST example"""
        self.implement_file_test(example_dir / "single_qubit_gst.jaqal")

    def test_hadamard_unitary_timed_gates(self):
        """Test visiting the hadamard program"""
        file_path = example_dir / "hadamard.jaqal"
        text = Path(file_path).read_text()
        Interface(text, allow_no_usepulses=True)
        
    def test_gst_unitary_timed_gates(self):
        """Test visiting the gst program"""
        file_path = example_dir / "single_qubit_gst.jaqal"
        text = Path(file_path).read_text()
        Interface(text, allow_no_usepulses=True)
 
