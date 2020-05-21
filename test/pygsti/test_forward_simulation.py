import unittest

import jaqal
from jaqal.core import ScheduledCircuit as Circuit
import numpy as np
import jaqal.pygsti
from qscout.gate_pulse import native_gates
from jaqal.generator import generate_jaqal_program
import jaqal.jaqal
from jaqal.core.circuit import normalize_native_gates


class ForwardSimulatorTester(unittest.TestCase):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        c = Circuit(native_gates.NATIVE_GATES)

        pi2 = c.let("pi2", np.pi / 2)
        q = c.reg("q", 3)

        c.gate("prepare_all")
        c.gate("MS", q[1], q[0], pi2, pi2)
        c.gate("measure_all")

        self.c = c

        self.jaqal_string = generate_jaqal_program(c)

        self.jaqal_c = jaqal.jaqal.parser.parse_jaqal_string(
            self.jaqal_string,
            native_gates=normalize_native_gates(native_gates=native_gates.NATIVE_GATES),
        )

    def test_generate_jaqal_program(self):

        self.assertEqual(
            self.jaqal_string,
            """register q[3]

let pi2 1.5707963267948966

prepare_all 
MS q[1] q[0] pi2 pi2
measure_all 
""",
        )

    def test_forward_simulate_circuit(self):
        c_dict = jaqal.pygsti.forward_simulate_circuit(self.c)
        self.assertAlmostEqual(c_dict["000"], 0.5)
        self.assertAlmostEqual(c_dict["001"], 0)
        self.assertAlmostEqual(c_dict["010"], 0)
        self.assertAlmostEqual(c_dict["011"], 0)
        self.assertAlmostEqual(c_dict["100"], 0)
        self.assertAlmostEqual(c_dict["101"], 0)
        self.assertAlmostEqual(c_dict["110"], 0.5)
        self.assertAlmostEqual(c_dict["111"], 0)

        jaqal_c_dict = jaqal.pygsti.forward_simulate_circuit(self.jaqal_c)
        self.assertAlmostEqual(jaqal_c_dict["000"], 0.5)
        self.assertAlmostEqual(jaqal_c_dict["001"], 0)
        self.assertAlmostEqual(jaqal_c_dict["010"], 0)
        self.assertAlmostEqual(jaqal_c_dict["011"], 0)
        self.assertAlmostEqual(jaqal_c_dict["100"], 0)
        self.assertAlmostEqual(jaqal_c_dict["101"], 0)
        self.assertAlmostEqual(jaqal_c_dict["110"], 0.5)
        self.assertAlmostEqual(jaqal_c_dict["111"], 0)

    def test_forward_simulate_circuit(self):
        c_count_dict = jaqal.pygsti.forward_simulate_circuit_counts(self.c, 1000)
        jaqal_c_count_dict = jaqal.pygsti.forward_simulate_circuit_counts(
            self.jaqal_c, 1000
        )
