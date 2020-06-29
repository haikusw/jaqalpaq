import os
import unittest, pytest

import numpy as np

from jaqalpaq import JaqalError
from jaqalpaq.emulator import run_jaqal_file
from jaqalpaq.core.result import ExecutionResult
from collections import OrderedDict

qscout = pytest.importorskip("qscout")

from qscout.v1 import native_gates


def example(*args):
    return os.path.join("examples", "jaqal", *args)


_fnames = [example(fn) for fn in os.listdir(example()) if fn[-6:] == ".jaqal"]


def pytest_generate_tests(metafunc):
    metafunc.parametrize("filename", [fn for fn in _fnames])


class TestExecuteAnnotatedJaqalFile:
    def test_jaqal_file(self, filename):
        expected = self.parse_comments(filename)

        try:
            exc, exc_message = expected["error"]
        except KeyError:
            pass
        else:
            with pytest.raises(exc) as excinfo:
                exe = run_jaqal_file(filename)
            assert exc_message == str(excinfo.value)
            return

        exe = run_jaqal_file(filename)

        try:
            true_str_list = expected["true_str_list"]
        except KeyError:
            pass
        else:
            true_int_list = expected["true_int_list"]
            subexp_list = expected["subexp_list"]

            assert true_str_list == exe.output()
            assert true_int_list == exe.output(fmt="int")

            for n, t_str in enumerate(true_str_list):
                assert t_str == exe.output(n)
                assert true_int_list[n] == exe.output(n, fmt="int")
                assert subexp_list[n] == exe.get_s_idx(n)

        try:
            str_prob = expected["str_prob"]
        except KeyError:
            pass
        else:
            for s_idx in range(len(exe.subexperiments)):
                for (ka, va), (kb, vb) in zip(
                    str_prob[s_idx].items(), exe.probabilities(s_idx, fmt="str").items()
                ):
                    assert ka == kb
                    assert np.isclose(va, vb)

        try:
            int_prob = expected["int_prob"]
        except KeyError:
            pass
        else:
            for s_idx in range(len(exe.subexperiments)):
                for (ka, va), (kb, vb) in zip(
                    int_prob[s_idx].items(),
                    enumerate(exe.probabilities(s_idx, fmt="int")),
                ):
                    assert ka == kb
                    assert np.isclose(va, vb)

    def parse_comments(self, filename):
        section = None
        expected = {}
        s_idx = None

        with open(filename, "r") as f:
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                line = line.strip()

                if line[:2] != "//":
                    s_idx = section = None
                    continue

                line = line[2:].strip()

                if len(line) == 0:
                    s_idx = section = None
                    continue

                if section == "meas":
                    true_str, true_int, subexp = line.split()
                    true_str_list.append(true_str)
                    true_int_list.append(int(true_int))
                    subexp_list.append(int(subexp))
                elif section == "prob":
                    if line[:14] == "SUBEXPERIMENT ":
                        s_idx = int(line[14:].strip())
                        str_prob[s_idx] = OrderedDict()
                        int_prob[s_idx] = OrderedDict()
                        continue

                    assert s_idx is not None
                    key_str, key_int, val = line.split()
                    val = float(val)
                    str_prob[s_idx][key_str] = val
                    int_prob[s_idx][int(key_int)] = val
                elif section == "error":
                    exc_name, exc_message = line.split(": ", 1)
                    if exc_name == "jaqalpaq.error.JaqalError":
                        exc = JaqalError
                    else:
                        raise NotImplementedError(
                            f"Unwhitelisted exception f{exc_name}"
                        )
                    expected["error"] = exc, exc_message
                elif line == "":
                    pass
                else:
                    assert section is None
                    if line == "EXPECTED MEASUREMENTS":
                        section = "meas"
                        true_str_list = expected["true_str_list"] = []
                        true_int_list = expected["true_int_list"] = []
                        subexp_list = expected["subexp_list"] = []
                    elif line == "EXPECTED PROBABILITIES":
                        section = "prob"
                        str_prob = expected["str_prob"] = {}
                        int_prob = expected["int_prob"] = {}
                    elif line == "EXPECTED ERROR":
                        section = "error"

        return expected
