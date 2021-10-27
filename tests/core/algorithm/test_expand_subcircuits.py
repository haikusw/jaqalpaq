import unittest

from jaqalpaq.core.algorithm.expand_subcircuits import expand_subcircuits
from jaqalpaq.parser import parse_jaqal_string
from jaqalpaq.core.circuitbuilder import build
import jaqalpaq.core as core


# Note: There are cases that the visitor can handle but that we either
# forbid or discourage, such as nesting a subcircuit block within a
# parallel block or another subcircuit block. No tests exist for these
# cases.


class ExpandSubcircuitsTester(unittest.TestCase):
    def test_noop(self):
        """Test expanding subcircuits in a circuit without any."""
        text = "{ foo; < bar | baz > }"
        exp_text = "{ foo; < bar | baz > }"
        self.run_test(text, exp_text)

    def test_empty_top_level(self):
        """Test a subcircuit block at the top level with no other
        gates."""
        text = "subcircuit {}"
        exp_text = "{prepare_all; measure_all}"
        self.run_test(text, exp_text)

    def test_ignore_iterations(self):
        """Test that a subcircuit with iterations has no effect on the output circuit."""
        text = "subcircuit 500 {}"
        exp_text = "{prepare_all; measure_all}"
        self.run_test(text, exp_text)

    def test_nonempty_top_level(self):
        """Test a subcircuit block at the top level with other gates."""
        text = "subcircuit { foo ; bar }"
        exp_text = "{ prepare_all; foo ; bar; measure_all }"
        self.run_test(text, exp_text)

    def test_multiple_top_level(self):
        """Test multiple subcircuits at the top level."""
        text = "subcircuit { foo ; bar}\nsubcircuit { baz ; qux }"
        exp_text = (
            "{ prepare_all; foo; bar; measure_all }\n"
            + "{ prepare_all; baz; qux; measure_all }"
        )
        self.run_test(text, exp_text)

    def test_sequential_block(self):
        """Test expanding a subcircuit block inside a sequential block."""
        # This one can't be expressed by legal Jaqal
        insexp = [
            "circuit",
            ["sequential_block", ["subcircuit_block", None, ["gate", "foo"]]],
        ]
        outsexp = [
            "circuit",
            [
                "sequential_block",
                [
                    "sequential_block",
                    ["gate", "prepare_all"],
                    ["gate", "foo"],
                    ["gate", "measure_all"],
                ],
            ],
        ]
        incirc = expand_subcircuits(build(insexp))
        outcirc = build(outsexp)
        if incirc != outcirc:
            print(incirc)
            print(outcirc)
        self.assertEqual(incirc, outcirc)

    def test_loop(self):
        """Test expanding a subcircuit block inside a loop."""
        # This one can't be expressed by legal Jaqal
        insexp = ["circuit", ["loop", 5, ["subcircuit_block", None, ["gate", "foo"]]]]
        outsexp = [
            "circuit",
            [
                "loop",
                5,
                [
                    "sequential_block",
                    ["gate", "prepare_all"],
                    ["gate", "foo"],
                    ["gate", "measure_all"],
                ],
            ],
        ]
        incirc = expand_subcircuits(build(insexp))
        outcirc = build(outsexp)
        if incirc != outcirc:
            print(incirc)
            print(outcirc)
        self.assertEqual(incirc, outcirc)

    def test_alternative_definitions(self):
        """Test providing your own measure and prepare gate defintions."""
        text = "subcircuit {}"
        exp_text = "{prep; meas}"
        prepare_def = core.GateDefinition("prep")
        measure_def = core.GateDefinition("meas")
        self.run_test(text, exp_text, prepare_def=prepare_def, measure_def=measure_def)

    def test_alternative_names(self):
        """Test providing different names for the prep and measure gates and
        having them created."""
        text = "subcircuit {}"
        exp_text = "{prep; meas}"
        self.run_test(text, exp_text, prepare_def="prep", measure_def="meas")

    def test_default_native_definition(self):
        """Test looking up default native definitions and using them."""
        native_gates = {
            "prepare_all": core.GateDefinition("prepare_all"),
            "measure_all": core.GateDefinition("measure_all"),
        }
        insexpr = ["circuit", ["subcircuit_block", None]]
        circ = build(insexpr, inject_pulses=native_gates)
        xcirc = expand_subcircuits(circ)
        self.assertIs(
            xcirc.body.statements[0].statements[0].gate_def, native_gates["prepare_all"]
        )
        self.assertIs(
            xcirc.body.statements[0].statements[-1].gate_def,
            native_gates["measure_all"],
        )

    def test_native_definition(self):
        """Test looking up renamed native definitions and using them."""
        native_gates = {
            "prep": core.GateDefinition("prep"),
            "meas": core.GateDefinition("meas"),
        }
        insexpr = ["circuit", ["subcircuit_block", None]]
        circ = build(insexpr, inject_pulses=native_gates)
        xcirc = expand_subcircuits(circ, prepare_def="prep", measure_def="meas")
        self.assertIs(
            xcirc.body.statements[0].statements[0].gate_def, native_gates["prep"]
        )
        self.assertIs(
            xcirc.body.statements[0].statements[-1].gate_def, native_gates["meas"]
        )

    def run_test(self, text, exp_text, prepare_def=None, measure_def=None):
        act_parsed = parse_jaqal_string(text, autoload_pulses=False)
        act_circuit = expand_subcircuits(
            act_parsed, prepare_def=prepare_def, measure_def=measure_def
        )
        if isinstance(exp_text, str):
            exp_circuit = parse_jaqal_string(exp_text, autoload_pulses=False)
        else:
            exp_circuit = build(exp_text)
        if exp_circuit != act_circuit:
            print(f"Expected:\n{exp_circuit}")
            print(f"Actual:\n{act_circuit}")
        self.assertEqual(exp_circuit, act_circuit)
