import unittest
from pathlib import Path
from test.test_parser import ParserTesterMixin

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
        self.implement_file_test("examples/hadamard.xqasm")
 
    def test_gst(self):
        """Test Singel Qubit GST example"""
        self.implement_file_test("examples/single_qubit_gst.xqasm")
 