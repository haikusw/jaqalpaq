import unittest, pytest

import jaqalpaq
from jaqalpaq.core.circuitbuilder import CircuitBuilder
import numpy as np
from jaqalpaq.emulator import run_jaqal_circuit
from jaqalpaq.generator import generate_jaqal_program
import jaqalpaq.parser
from jaqalpaq.core.circuit import normalize_native_gates

qscout = pytest.importorskip("qscout")

from qscout.v1 import native_gates


class ForwardSimulatorTester(unittest.TestCase):
    def setUp(self):

        builder = CircuitBuilder(native_gates.NATIVE_GATES)

        pi2 = builder.let("pi2", np.pi / 2)
        q = builder.register("q", 3)

        builder.gate("prepare_all")
        builder.gate("MS", q[1], q[0], pi2, pi2)
        builder.gate("measure_all")

        self.c = builder.build()

        self.jaqal_string = generate_jaqal_program(self.c)

        self.jaqal_c = jaqalpaq.parser.parse_jaqal_string(
            self.jaqal_string,
            inject_pulses=normalize_native_gates(native_gates.NATIVE_GATES),
        )

    def test_generate_jaqal_program(self):
        self.assertEqual(
            "\n".join([p.strip() for p in self.jaqal_string.split("\n")]),
            """let pi2 1.5707963267948966

register q[3]

prepare_all
MS q[1] q[0] pi2 pi2
measure_all
""",
        )

    def test_forward_simulate_circuit(self):
        for c in [self.c, self.jaqal_c]:
            res = run_jaqal_circuit(c)

            c_dict = res.probabilities(0, fmt="str")
            self.assertAlmostEqual(c_dict["000"], 0.5)
            self.assertAlmostEqual(c_dict["001"], 0)
            self.assertAlmostEqual(c_dict["010"], 0)
            self.assertAlmostEqual(c_dict["011"], 0)
            self.assertAlmostEqual(c_dict["100"], 0)
            self.assertAlmostEqual(c_dict["101"], 0)
            self.assertAlmostEqual(c_dict["110"], 0.5)
            self.assertAlmostEqual(c_dict["111"], 0)

    def test_five_qubit_GHZ(self):
        jaqal_text = """
register q[5]

let pi2 1.5707963267948966
let mpi2 -1.5707963267948966

macro CNOT control target {
Ry control pi2
MS control target 0 pi2
Rx target mpi2
Rx control mpi2
Ry control mpi2
}

prepare_all

Rx q[0] pi2

CNOT q[0] q[1]
CNOT q[1] q[2]
CNOT q[2] q[3]
CNOT q[3] q[4]

measure_all
"""
        jaqal_prog = jaqalpaq.parser.parse_jaqal_string(
            jaqal_text, inject_pulses=normalize_native_gates(native_gates.NATIVE_GATES)
        )
        res = run_jaqal_circuit(jaqal_prog)
        output_probs = res.probabilities(0, fmt="str")
        self.assertAlmostEqual(output_probs["00000"], 0.5)
        self.assertAlmostEqual(output_probs["11111"], 0.5)

    @unittest.skip("Multiple registers not allowed in Jaqal spec")
    def test_multiple_registers(self):
        jaqal_text = """
register p[3]
register q[2]

let pi2 1.5707963267948966
let mpi2 -1.5707963267948966

macro CNOT control target {
Ry control pi2
MS control target 0 pi2
Rx target mpi2
Rx control mpi2
Ry control mpi2
}

prepare_all

Rx p[0] pi2

CNOT p[0] p[1]
CNOT p[1] p[2]
CNOT p[2] q[0]
CNOT q[0] q[1]

measure_all
"""
        jaqal_prog = jaqalpaq.parser.parse_jaqal_string(
            jaqal_text, inject_pulses=normalize_native_gates(native_gates.NATIVE_GATES)
        )
        res = run_jaqal_circuit(jaqal_prog)
        output_probs = res.probabilities(0, fmt="str")
        self.assertAlmostEqual(output_probs["00000"], 0.5)
        self.assertAlmostEqual(output_probs["11111"], 0.5)

    @unittest.skip("Multiple registers not allowed in Jaqal spec")
    def test_multiple_registers_and_ancilla(self):
        jaqal_text = """
register p[3]
register q[2]
map ancilla q[1]

let pi2 1.5707963267948966
let mpi2 -1.5707963267948966

macro CNOT control target {
Ry control pi2
MS control target 0 pi2
Rx target mpi2
Rx control mpi2
Ry control mpi2
}

prepare_all

Rx p[0] pi2

CNOT p[0] p[1]
CNOT p[1] p[2]
CNOT p[2] q[0]
CNOT q[0] ancilla

measure_all
"""
        jaqal_prog = jaqalpaq.parser.parse_jaqal_string(
            jaqal_text, inject_pulses=normalize_native_gates(native_gates.NATIVE_GATES)
        )
        res = run_jaqal_circuit(jaqal_prog)
        output_probs = res.probabilities(0, fmt="str")
        self.assertAlmostEqual(output_probs["00000"], 0.5)
        self.assertAlmostEqual(output_probs["11111"], 0.5)

    @unittest.skip("Multiple registers not allowed in Jaqal spec")
    def test_multiple_registers_and_ancillae(self):
        jaqal_text = """
register p[3]
register q[3]
map ancillae q[0:2]

let pi2 1.5707963267948966
let mpi2 -1.5707963267948966

macro CNOT control target {
Ry control pi2
MS control target 0 pi2
Rx target mpi2
Rx control mpi2
Ry control mpi2
}

prepare_all

Rx p[0] pi2

CNOT p[0] p[1]
CNOT p[1] p[2]
CNOT p[2] ancillae[0]
CNOT ancillae[0] ancillae[1]
CNOT ancillae[1] q[2]

measure_all
"""
        jaqal_prog = jaqalpaq.parser.parse_jaqal_string(
            jaqal_text, inject_pulses=normalize_native_gates(native_gates.NATIVE_GATES)
        )
        res = run_jaqal_circuit(jaqal_prog)
        output_probs = res.probabilities(0, fmt="str")
        self.assertAlmostEqual(output_probs["000000"], 0.5)
        self.assertAlmostEqual(output_probs["111111"], 0.5)
