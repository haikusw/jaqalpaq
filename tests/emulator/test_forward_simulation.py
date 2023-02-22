import unittest, pytest
import os

import jaqalpaq
import jaqalpaq.error
from jaqalpaq.core.circuitbuilder import CircuitBuilder
import numpy as np
from jaqalpaq.emulator import run_jaqal_string, run_jaqal_circuit, run_jaqal_file
from jaqalpaq.generator import generate_jaqal_program
import jaqalpaq.parser
from jaqalpaq.core.result import ExecutionResult, parse_jaqal_output_list
from collections import OrderedDict
from jaqalpaq.emulator._validator import (
    generate_jaqal_validation,
    validate_jaqal_string,
)
from jaqalpaq.emulator.pygsti.circuit import pygsti_circuit_from_circuit

qscout = pytest.importorskip("qscout")

from qscout.v1.std import jaqal_gates
from qscout.v1.std.noisy import SNLToy1


def example(*args):
    return os.path.join("examples", "jaqal", *args)


class ForwardSimulatorTester(unittest.TestCase):
    def setUp(self):
        builder = CircuitBuilder(jaqal_gates.ALL_GATES)

        pi2 = builder.let("pi2", np.pi / 2)
        q = builder.register("q", 3)

        builder.gate("prepare_all")
        builder.gate("MS", q[1], q[0], pi2, pi2)
        builder.gate("measure_all")

        self.c = builder.build()

        self.jaqal_string = generate_jaqal_program(self.c)

        self.jaqal_c = jaqalpaq.parser.parse_jaqal_string(
            self.jaqal_string,
            inject_pulses=jaqal_gates.ALL_GATES,
        )

    def test_generate_jaqal_program(self):
        self.assertEqual(
            "\n".join([p for p in self.jaqal_string.split("\n")]),
            """let pi2 1.5707963267948966

register q[3]

prepare_all
MS q[1] q[0] pi2 pi2
measure_all
""",
        )

    def test_forward_simulate_circuit(self):
        for c in [self.c, self.jaqal_c]:
            res = run_jaqal_string(
                "\n".join(("from qscout.v1.std usepulses *", self.jaqal_string))
            )

            for c_dict in (
                res.subcircuits[0].probability_by_str,
                res.subcircuits[0].simulated_probability_by_str,
            ):
                self.assertAlmostEqual(c_dict["000"], 0.5)
                self.assertAlmostEqual(c_dict["001"], 0)
                self.assertAlmostEqual(c_dict["010"], 0)
                self.assertAlmostEqual(c_dict["011"], 0)
                self.assertAlmostEqual(c_dict["100"], 0)
                self.assertAlmostEqual(c_dict["101"], 0)
                self.assertAlmostEqual(c_dict["110"], 0.5)
                self.assertAlmostEqual(c_dict["111"], 0)

    def test_emulate_subcircuit(self):
        jaqal_string = """let pi2 1.5707963267948966

register q[3]

subcircuit {
  MS q[1] q[0] pi2 pi2
}
"""
        res = run_jaqal_string(
            "\n".join(("from qscout.v1.std usepulses *", jaqal_string))
        )

        c_dict = res.subcircuits[0].probability_by_str
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
            jaqal_text, inject_pulses=jaqal_gates.ALL_GATES
        )
        res = run_jaqal_circuit(jaqal_prog)
        output_probs = res.subcircuits[0].probability_by_str
        self.assertAlmostEqual(output_probs["00000"], 0.5)
        self.assertAlmostEqual(output_probs["11111"], 0.5)

    def test_JaqalError(self):
        with pytest.raises(jaqalpaq.error.JaqalError):
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
        probs = results.subcircuits[0].probability_by_str
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
            i: p.probability_by_str for i, p in enumerate(results.subcircuits)
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
        for i in range(len(results.subcircuits)):
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
        output = [o.as_str for o in results.readouts]
        true_output = ["10", "10", "01", "01"]
        self.assertEqual(output, true_output)

    def test_interleaved_bit_flip(self):
        jaqal_str = """
from qscout.v1.std usepulses *

register q[3]
loop 2 {
    prepare_all
    Px q[0]
    measure_all
    loop 2 {
        prepare_all
        Px q[1]
        measure_all
    }
}

prepare_all
Px q[2]
prepare_all
Px q[2]
measure_all
"""
        results = jaqalpaq.emulator.run_jaqal_string(jaqal_str)
        output = [o.as_str for o in results.readouts]
        int_output = [o.as_int for o in results.readouts]
        true_output = ["100", "010", "010", "100", "010", "010", "001"]
        true_int_output = [1, 2, 2, 1, 2, 2, 4]
        self.assertEqual(output, true_output)
        self.assertEqual(int_output, true_int_output)

        int_output = [o.as_int for o in results.subcircuits[0].readouts]
        output = [o.as_str for o in results.subcircuits[0].readouts]
        self.assertEqual(int_output, [1, 1])
        self.assertEqual(output, ["100", "100"])

        int_output = [o.as_int for o in results.subcircuits[1].readouts]
        output = [o.as_str for o in results.subcircuits[1].readouts]
        self.assertEqual(int_output, [2, 2, 2, 2])
        self.assertEqual(output, ["010", "010", "010", "010"])

        int_output = [o.as_int for o in results.subcircuits[2].readouts]
        output = [o.as_str for o in results.subcircuits[2].readouts]
        self.assertEqual(int_output, [4])
        self.assertEqual(output, ["001"])

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
            i: p.probability_by_str for i, p in enumerate(results.subcircuits)
        }
        true_prob_dicts = {
            0: OrderedDict([("0", 0.9975923633363278), ("1", 0.0024076366636721458)]),
            1: OrderedDict([("0", 0.9903926402064304), ("1", 0.009607359793569742)]),
            2: OrderedDict([("0", 0.978470167862337), ("1", 0.02152983213766301)]),
            3: OrderedDict([("0", 0.9619397662553992), ("1", 0.03806023374460075)]),
        }
        for i in range(len(results.subcircuits)):
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
        output = [o.as_str for o in results.readouts]
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

        # We do not yet support reuse
        # exe_reuse = parse_jaqal_output_list(results._circuit, true_output)
        exe = parse_jaqal_output_list(parsed_jaqal_str, true_output)
        self.assertEqual(true_output, [o.as_str for o in results.readouts])
        self.assertEqual(true_output, [o.as_str for o in exe.readouts])
        # self.assertEqual(true_output, [o.as_str for o in exe_reuse.readouts])

    def test_load_jaqal_file(self):
        fname = example("sequential_block_in_parallel_loop.jaqal")
        exe = run_jaqal_file(fname)
        newval = generate_jaqal_validation(exe)

        with open(fname, "r") as f:
            txt = [a for a in f.readlines() if not a.startswith("//")]

        txt.append(newval)
        txt = "".join(txt)

        res = validate_jaqal_string(txt)

        self.assertEqual(res, ["measurements agree", "probabilities agree"])

    def test_stretched_gates(self):
        jc = jaqalpaq.parser.parse_jaqal_string(
            """
            from qscout.v1.std usepulses *
            from qscout.v1.std.stretched usepulses *

            register u[3]

            prepare_all

            Rx u[0] 0.7
            Rx_stretched u[0] 0.7 1.5

            MS u[0] u[1] 0.1 0.3
            MS_stretched u[0] u[2] 0.1 0.3 3

            Rz_stretched u[2] 0.8 2.0

            measure_all
        """
        )

        backend = SNLToy1(3, stretched_gates="add")

        pc = pygsti_circuit_from_circuit(jc, durations=backend.gate_durations)

        # Check that idles are performed on qubit 2 and 3 during Rx
        p_rx_id1 = pc[1]
        p_rx_id2 = pc[2]
        self.assertEqual(p_rx_id1.name, "Gidle")
        self.assertEqual(p_rx_id2.name, "Gidle")
        (rx_dur_1,) = p_rx_id1.args
        (rx_dur_2,) = p_rx_id2.args
        self.assertAlmostEqual(rx_dur_1, rx_dur_2)

        # Check that idles are performed on qubit 2 and 3 during Rx_stretched
        p_rx_stretched_id1 = pc[4]
        p_rx_stretched_id2 = pc[5]
        self.assertEqual(p_rx_stretched_id1.name, "Gidle")
        self.assertEqual(p_rx_stretched_id2.name, "Gidle")
        (rx_stretched_dur_1,) = p_rx_stretched_id1.args
        (rx_stretched_dur_2,) = p_rx_stretched_id2.args
        self.assertAlmostEqual(rx_stretched_dur_1, rx_stretched_dur_2)

        # Check that the idle is of stretched duration
        self.assertAlmostEqual(rx_stretched_dur_1, rx_dur_1 * 1.5)

        # Check that an idle is performed on qubit 2 during MS
        p_ms_id = pc[7]
        self.assertEqual(p_ms_id.name, "Gidle")
        (ms_dur,) = p_ms_id.args

        # Check that an idle is performed on qubit 2 during MS_stretched
        p_ms_stretched_id = pc[9]
        self.assertEqual(p_ms_stretched_id.name, "Gidle")
        (ms_stretched_dur,) = p_ms_stretched_id.args

        # Check that the idle is of stretched duration
        self.assertAlmostEqual(ms_dur * 3, ms_stretched_dur)

        # There should be no zero-length idles in parallel with the Rz
        self.assertEqual(len(pc), 11)

    def test_idle_padding(self):
        with open(example("idle_padding.jaqal"), "r") as f:
            content = f.read()

        from jaqalpaq.emulator.pygsti import backends
        from pygsti.baseobjs.label import LabelTupTup, LabelTupWithArgs

        orig_KPO = backends.KEEP_PYGSTI_OBJECTS
        backends.KEEP_PYGSTI_OBJECTS = True

        try:
            circ = jaqalpaq.parser.parse_jaqal_string(content)

            backend = SNLToy1(3, rotation_error=0, depolarization=0.1)
            exe_res = run_jaqal_circuit(circ, backend=backend)
            sc = exe_res.subcircuits[0]

            probs = sc.probability_by_int
            self.assertAlmostEqual(probs[0], 0.48055181)
            self.assertAlmostEqual(probs[1], 0.16081769)
            self.assertAlmostEqual(probs[2], 0.23973497)
            self.assertAlmostEqual(probs[3], 0.08022782)
            self.assertAlmostEqual(probs[4], 0.01932925)
            self.assertAlmostEqual(probs[5], 0.00646858)
            self.assertAlmostEqual(probs[6], 0.00964287)
            self.assertAlmostEqual(probs[7], 0.00322701)

            pc = sc._pygsti_circuit
            # This checks that there are three "layers" of pygsti gates.
            self.assertEqual(len(pc), 3)

            # This checks that the first layer has two gates:
            self.assertIsInstance(pc[0], LabelTupTup)
            self.assertEqual(len(pc[0]), 2)

            ref = {0: "GJRx", 1: "GJRx"}
            # an Rx applied to qubit 0;
            # an Rx applied to qubit 1;
            # and an idle applied to qubit 2.

            # But, the order of the gates in this layer is irrelevant:
            dkt = {}
            for op in pc[0]:
                self.assertIsInstance(op, LabelTupWithArgs)
                (qubit,) = op.qubits
                assert qubit not in dkt
                dkt[qubit] = op.name

            self.assertEqual(dkt, ref)

            # This checks that the second layer has a single gate:
            self.assertEqual(len(pc[1]), 1)

            self.assertEqual(pc[1][0].name, "Gidle")
            self.assertEqual(pc[1][0].qubits, (0,))
            self.assertEqual(pc[1][0].args, (0.1273239544735162,))
            # an idle applied to qubit 0.

            # This checks that the third layer has one gate:
            self.assertIsInstance(pc[2], LabelTupWithArgs)

            self.assertEqual(pc[2].name, "Gidle")
            self.assertEqual(pc[2].qubits, (2,))
            self.assertEqual(pc[2].args, (0.7639437268410976,))
            # an idle applied to qubit 2
        finally:
            backends.KEEP_PYGSTI_OBJECTS = orig_KPO

    def test_idle(self):
        with open(example("only_idles.jaqal"), "r") as f:
            content = f.read()

        from jaqalpaq.emulator.pygsti import backends

        circ = jaqalpaq.parser.parse_jaqal_string(content)

        backend = SNLToy1(2, rotation_error=0, depolarization=0.1)
        exe_res = run_jaqal_circuit(circ, backend=backend)
        sc = exe_res.subcircuits[0]

        probs = sc.probability_by_int
        self.assertAlmostEqual(probs[0], 0.36710198608176264)
        self.assertAlmostEqual(probs[1], 0.23878743128890134)
        self.assertAlmostEqual(probs[2], 0.23878743128890134)
        self.assertAlmostEqual(probs[3], 0.15532315134043467)
