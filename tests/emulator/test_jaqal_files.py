import os
import unittest, pytest

import numpy as np

from jaqalpaq.emulator._validator import validate_jaqal_string

qscout = pytest.importorskip("qscout")

from qscout.v1 import native_gates


def example(*args):
    return os.path.join("examples", "jaqal", *args)


_fnames = [example(fn) for fn in os.listdir(example()) if fn[-6:] == ".jaqal"]


def pytest_generate_tests(metafunc):
    metafunc.parametrize("filename", [fn for fn in _fnames])


class TestExecuteAnnotatedJaqalFile:
    def test_jaqal_file(self, filename):
        with open(filename, "r") as f:
            validate_jaqal_string(f.read())
