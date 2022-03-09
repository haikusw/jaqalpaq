import os
import unittest, pytest

import numpy as np

from jaqalpaq.parser import parse_jaqal_string
from jaqalpaq.emulator._validator import (
    validate_jaqal_circuit,
    parse_jaqal_validation,
    validate_jaqal_parse,
)
from jaqalpaq.emulator.pygsti import CircuitEmulator
from jaqalpaq.emulator.pygsti.circuit import pygsti_circuit_from_circuit
from jaqalpaq.emulator.pygsti.model import build_noiseless_native_model

qscout = pytest.importorskip("qscout")

from qscout.v1.std.noisy import SNLToy1


def example(*args):
    return os.path.join("examples", "jaqal", *args)


_fnames = [example(fn) for fn in os.listdir(example()) if fn[-6:] == ".jaqal"]


def pytest_generate_tests(metafunc):
    metafunc.parametrize("filename", [fn for fn in _fnames])


class TestExecuteAnnotatedJaqalFile:
    def test_jaqal_file(self, filename):
        with open(filename, "r") as f:
            txt = f.read()

        expected = parse_jaqal_validation(txt)
        ret = validate_jaqal_parse(txt, expected)

        if isinstance(ret, list):
            return ret

        circ = ret

        validate_jaqal_circuit(circ, expected)

        (reg,) = circ.fundamental_registers()
        n = reg.size

        backend = SNLToy1(
            n,
            depolarization=0,
            rotation_error=0,
            phase_error=0,
        )

        validate_jaqal_circuit(circ, expected, backend=backend)

        validate_jaqal_circuit(
            circ,
            expected,
            backend=CircuitEmulator(
                model=build_noiseless_native_model(
                    n, circ.native_gates, evotype="default"
                ),
                gate_durations=backend.gate_durations,
            ),
        )

        backend = SNLToy1(
            n,
            depolarization=0,
            rotation_error=0,
            phase_error=0,
            stretched_gates=1,
        )

        validate_jaqal_circuit(circ, expected, backend=backend)

        validate_jaqal_circuit(
            circ,
            expected,
            backend=CircuitEmulator(
                model=build_noiseless_native_model(
                    n, circ.native_gates, evotype="default"
                ),
                gate_durations=backend.gate_durations,
            ),
        )
