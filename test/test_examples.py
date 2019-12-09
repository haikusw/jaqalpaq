import unittest
from pathlib import Path
from iqasm.testing.mixin import ParserTesterMixin

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
            parser.parse(text)
        except Exception as e: 
            raise AssertionError(f"{file_name}: {e}")

    def test_hadamard(self):
        """Test Hadamard example"""
        self.implement_file_test(example_dir / "hadamard.xqasm")
 
    def test_gst(self):
        """Test Single Qubit GST example"""
        self.implement_file_test(example_dir / "single_qubit_gst.xqasm")
