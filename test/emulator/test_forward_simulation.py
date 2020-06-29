import unittest, pytest

import jaqalpaq
from jaqalpaq.core.circuitbuilder import CircuitBuilder
import numpy as np
from jaqalpaq.emulator import run_jaqal_circuit
from jaqalpaq.generator import generate_jaqal_program
import jaqalpaq.parser
from jaqalpaq.core.circuit import normalize_native_gates
from jaqalpaq.core.result import ExecutionResult
from collections import OrderedDict

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

    def test_JaqalError(self):
        with pytest.raises(jaqalpaq.JaqalError):
            jaqal_str = """
from qscout.v1.std usepulses *
register q[1]
prepare_all
Px q[0]
measure_all
measure_all
"""
            jaqal_circ = jaqalpaq.parser.parse_jaqal_string(jaqal_str)
            results = jaqalpaq.emulator.run_jaqal_circuit(jaqal_circ)

    def test_spec_bell_state(self):
        jaqal_str = """
from qscout.v1.std usepulses *

register q[2]

let pi2 1.5707963267948966
let pi4 0.7853981633974483

macro hadamard target { // A Hadamard gate can be implemented as
    Sy target           // a pi/2 rotation around Y
    Px target           // followed by a pi rotation around X.
}
macro cnot control target {  // CNOT implementation from Maslov (2017)
    Sy control               //
    MS control target 0 pi2
    <Sxd control | Sxd target>  // we can perform these in parallel
    Syd control
}

prepare_all
hadamard q[0]
cnot q[0] q[1]
measure_all
"""
        results = jaqalpaq.emulator.run_jaqal_string(jaqal_str)
        probs = results.probabilities(0)
        true_probs = OrderedDict({"00": 0.5, "01": 0, "10": 0, "11": 0.5})
        for key in true_probs:
            self.assertAlmostEqual(probs[key], true_probs[key])

    def test_spec_single_qubit_gst(self):
        jaqal_str = """
from qscout.v1.std usepulses *

register q[1]

macro F0 qubit { }  // Fiducials
macro F1 qubit { Sx qubit }
macro F2 qubit { Sy qubit }
macro F3 qubit { Sx qubit; Sx qubit}
macro F4 qubit { Sx qubit; Sx qubit; Sx qubit }
macro F5 qubit { Sy qubit; Sy qubit; Sy qubit }

macro G0 qubit { Sx qubit }  // Germs
macro G1 qubit { Sy qubit }
macro G2 qubit { I_Sx qubit }
macro G3 qubit { Sx qubit; Sy qubit }
macro G4 qubit { Sx qubit; Sy qubit; I_Sx qubit }
macro G5 qubit { Sx qubit; I_Sx qubit; Sy qubit }
macro G6 qubit { Sx qubit; I_Sx qubit; I_Sx qubit }
macro G7 qubit { Sy qubit; I_Sx qubit; I_Sx qubit }
macro G8 qubit { Sx qubit; Sx qubit; I_Sx qubit; Sy qubit }
macro G9 qubit { Sx qubit; Sy qubit; Sy qubit; I_Sx qubit }
macro G10 qubit { Sx qubit; Sx qubit; Sy qubit; Sx qubit; Sy qubit; Sy qubit }

prepare_all  // Length 1
F0 q[0]
measure_all

prepare_all
F1 q[0]
measure_all

prepare_all
F2 q[0]
measure_all

prepare_all
F3 q[0]
measure_all

prepare_all
F4 q[0]
measure_all

prepare_all
F5 q[0]
measure_all

prepare_all
F1 q[0]; F1 q[0]
measure_all

prepare_all
F1 q[0]; F2 q[0]
measure_all

prepare_all
F1 q[0]
loop 8 { G1 q[0] }
F1 q[0]
measure_all
"""
        results = jaqalpaq.emulator.run_jaqal_string(jaqal_str)
        prob_dicts = {
            i: results.probabilities(i) for i in range(len(results.subexperiments))
        }
        true_prob_dicts = {
            0: OrderedDict([("0", 1.0), ("1", 0.0)]),
            1: OrderedDict([("0", 0.5), ("1", 0.5)]),
            2: OrderedDict([("0", 0.5), ("1", 0.5)]),
            3: OrderedDict([("0", 0), ("1", 1.0)]),
            4: OrderedDict([("0", 0.5), ("1", 0.5)]),
            5: OrderedDict([("0", 0.5), ("1", 0.5)]),
            6: OrderedDict([("0", 0.0), ("1", 1.0)]),
            7: OrderedDict([("0", 0.5), ("1", 0.5)]),
            8: OrderedDict([("0", 0.0), ("1", 1.0)]),
        }
        for i in range(len(results.subexperiments)):
            for key in true_prob_dicts[i].keys():
                self.assertAlmostEqual(prob_dicts[i][key], true_prob_dicts[i][key])

    def test_bit_flip(self):
        jaqal_str = """
from qscout.v1.std usepulses *

register q[2]
loop 2 {
    prepare_all
Px q[0]
    measure_all
}
loop 2 {
    prepare_all
Px q[1]
    measure_all
}
"""
        results = jaqalpaq.emulator.run_jaqal_string(jaqal_str)
        output = results.output()
        true_output = ["10", "10", "01", "01"]
        self.assertEqual(output, true_output)

    def test_spec_pi_fracs(self):
        jaqal_str = """
from qscout.v1.std usepulses *

register q[1]
let pi_32   0.09817477042
let pi_16   0.1963495408
let pi_3_32 0.2945243113
let pi_8    0.3926990817

prepare_all
Ry q[0] pi_32
measure_all
prepare_all
Ry q[0] pi_16
measure_all
prepare_all
Ry q[0] pi_3_32
measure_all
prepare_all
Ry q[0] pi_8
measure_all
"""

        results = jaqalpaq.emulator.run_jaqal_string(jaqal_str)
        prob_dicts = {
            i: results.probabilities(i) for i in range(len(results.subexperiments))
        }
        true_prob_dicts = {
            0: OrderedDict([("0", 0.9975923633363278), ("1", 0.0024076366636721458)]),
            1: OrderedDict([("0", 0.9903926402064304), ("1", 0.009607359793569742)]),
            2: OrderedDict([("0", 0.978470167862337), ("1", 0.02152983213766301)]),
            3: OrderedDict([("0", 0.9619397662553992), ("1", 0.03806023374460075)]),
        }
        for i in range(len(results.subexperiments)):
            for key in true_prob_dicts[i].keys():
                self.assertAlmostEqual(prob_dicts[i][key], true_prob_dicts[i][key])

    def test_nested_bit_flips(self):
        jaqal_str = """
from qscout.v1.std usepulses *

register q[4]

loop 2 {
    prepare_all
    Px q[0]
    measure_all
    loop 2 {
        prepare_all
        Px q[0]
        Px q[1]
        measure_all
        loop 2 {
            prepare_all
            Px q[0]
            Px q[1]
            Px q[2]
            measure_all
            loop 2 {
                prepare_all
                Px q[0]
                Px q[1]
                Px q[2]
                Px q[3]
                measure_all
                    }
                }
            }
        }
"""
        results = jaqalpaq.emulator.run_jaqal_string(jaqal_str)
        output = results.output()
        true_output = [
            "1000",
            "1100",
            "1110",
            "1111",
            "1111",
            "1110",
            "1111",
            "1111",
            "1100",
            "1110",
            "1111",
            "1111",
            "1110",
            "1111",
            "1111",
            "1000",
            "1100",
            "1110",
            "1111",
            "1111",
            "1110",
            "1111",
            "1111",
            "1100",
            "1110",
            "1111",
            "1111",
            "1110",
            "1111",
            "1111",
        ]
        self.assertEqual(output, true_output)

        parsed_jaqal_str = jaqalpaq.parser.parse_jaqal_string(jaqal_str)

        exe_reuse = ExecutionResult(results, output=true_output)
        exe = ExecutionResult(parsed_jaqal_str, output=true_output)
        self.assertEqual(true_output, results.output())
        self.assertEqual(true_output, exe.output())
        self.assertEqual(true_output, exe_reuse.output())

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
