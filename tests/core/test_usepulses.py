import unittest
import warnings
from pathlib import Path

from jaqalpaq.error import JaqalError
from jaqalpaq.parser import parse_jaqal_string
import jaqalpaq.core as core


class UsepulsesTester(unittest.TestCase):
    def test_usepulses(self):
        """Test that usepulses correctly loads pulses into native_gates."""
        text = "from tests.core.gpf1 usepulses *"
        jc = parse_jaqal_string(text, autoload_pulses=True)
        from tests.core.gpf1 import jaqal_gates as ng1

        self.assertTrue(jc.native_gates["testgate"] is ng1.ALL_GATES["testgate"])

        (usepulses,) = jc.usepulses

        self.assertEqual(repr(usepulses), "UsePulsesStatement('tests.core.gpf1', '*')")
        self.assertEqual(str(usepulses.module), "tests.core.gpf1")
        self.assertEqual(usepulses.names, all)

    def test_usepulses_relative(self):
        """Test that usepulses correctly loads pulses into NATIVE_GATES
        when referenced relatively"""
        try:
            import gpf1
        except ImportError:
            pass
        else:
            warnings.warn('Unexepected module named "gpf1" will interfere with tests.')
            return

        text = "from .gpf1 usepulses *"
        jc = parse_jaqal_string(text, autoload_pulses=True, filename=__file__)
        from gpf1 import jaqal_gates as ng1

        self.assertTrue(jc.native_gates["testgate"] is ng1.ALL_GATES["testgate"])

        (usepulses,) = jc.usepulses

        self.assertEqual(repr(usepulses), "UsePulsesStatement('.gpf1', '*')")
        self.assertEqual(str(usepulses.module), ".gpf1")
        self.assertEqual(usepulses.names, all)

    def test_usepulses_reload(self):
        """Test that usepulses correctly reloads pulses into NATIVE_GATES
        when referenced relatively"""
        text = "from .gpf1 usepulses *"
        jc = parse_jaqal_string(text, autoload_pulses=True, filename=__file__)
        self.assertTrue("testgate" in jc.native_gates)
        self.assertTrue("reloadedtestgate" not in jc.native_gates)

        second = Path(__file__).parent / "reload" / "fake.jaqal"
        jc2 = parse_jaqal_string(text, autoload_pulses=True, filename=str(second))
        self.assertTrue("testgate" not in jc2.native_gates)
        self.assertTrue("reloadedtestgate" in jc2.native_gates)

    def test_multiple_usepulses(self):
        """Test multiple usepulses statements cause the correct overwrite."""
        text = """
            from tests.core.gpf1 usepulses *
            from tests.core.gpf2 usepulses *
        """
        jc = parse_jaqal_string(text, autoload_pulses=True)
        jc2 = parse_jaqal_string(text, autoload_pulses=True)
        from tests.core.gpf1 import jaqal_gates as ng1
        from tests.core.gpf2 import jaqal_gates as ng2

        self.assertIs(jc.native_gates["testgate"], ng2.ALL_GATES["testgate"])
        self.assertEqual(len(ng2.ALL_GATES["testgate"].parameters), 2)
        self.assertEqual(len(ng1.ALL_GATES["testgate"].parameters), 1)

        up0, up1 = jc.usepulses
        self.assertNotEqual(up0, up1)

        self.assertEqual(jc2.usepulses[1], up1)
        self.assertEqual(hash(jc2.usepulses[1]), hash(up1))
        self.assertEqual(jc2.usepulses[0], up0)
        self.assertEqual(hash(jc2.usepulses[0]), hash(up0))

    def test_multiple_usepulses_other(self):
        """Test multiple usepulses statements (in the reverse order) cause the correct
        overwrite."""
        text = """
            from tests.core.gpf2 usepulses *
            from tests.core.gpf1 usepulses *
        """
        jc = parse_jaqal_string(text, autoload_pulses=True)
        from tests.core.gpf1 import jaqal_gates as ng1
        from tests.core.gpf2 import jaqal_gates as ng2

        self.assertIs(jc.native_gates["testgate"], ng1.ALL_GATES["testgate"])
        self.assertEqual(len(ng1.ALL_GATES["testgate"].parameters), 1)
        self.assertEqual(len(ng2.ALL_GATES["testgate"].parameters), 2)
