import unittest
from pathlib import Path
from iqasm.testing.mixin import ParserTesterMixin

from iqasm.iter_gates import parse_unitary_timed_gates

top_example_dir = Path('examples')
test_example_dir = Path('../examples')

if top_example_dir.exists():
    example_dir = top_example_dir
elif test_example_dir.exists():
    example_dir = test_example_dir
else:
    raise IOError('Cannot find example directory')


class ExampleFileTester(ParserTesterMixin, unittest.TestCase):

    def implement_file_test(self, file_name):
        text = Path(file_name).read_text()
        parser = self.make_parser()
        try:
            tree = parser.parse(text)
        except Exception as e: 
            raise AssertionError(f"{file_name}: {e}")
        return tree

    def test_hadamard(self):
        """Test Hadamard example"""
        self.implement_file_test(example_dir / "hadamard.xqasm")
 
    def test_gst(self):
        """Test Single Qubit GST example"""
        self.implement_file_test(example_dir / "single_qubit_gst.xqasm")

    def test_hadamard_unitary_timed_gates(self):
        """Test visiting the hadamard program"""
        file_path = example_dir / "hadamard.xqasm"
        text = Path(file_path).read_text()
        parse_unitary_timed_gates(text)
        
    def test_gst_unitary_timed_gates(self):
        """Test visiting the gst program"""
        file_path = example_dir / "single_qubit_gst.xqasm"
        text = Path(file_path).read_text()
        parse_unitary_timed_gates(text)
 