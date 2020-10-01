import unittest

from jaqalpaq import JaqalError
from jaqalpaq.parser import parse_jaqal_string
import jaqalpaq.core as core


class UsepulsesTester(unittest.TestCase):
    def test_usepulses(self):
        """Test that usepulses correctly loads pulses into NATIVE_GATES."""
        text = "from tests.core.gpf1 usepulses *"
        jc = parse_jaqal_string(text, autoload_pulses=True)
        from tests.core.gpf1 import NATIVE_GATES as ng1

        self.assertTrue(jc.native_gates["testgate"] is ng1["testgate"])

    def test_multiple_usepulses(self):
        """Test multiple usepulses statements cause the correct overwrite."""
        text = """
            from tests.core.gpf1 usepulses *
            from tests.core.gpf2 usepulses *
        """
        jc = parse_jaqal_string(text, autoload_pulses=True)
        from tests.core.gpf1 import NATIVE_GATES as ng1
        from tests.core.gpf2 import NATIVE_GATES as ng2

        self.assertIs(jc.native_gates["testgate"], ng2["testgate"])
        self.assertEqual(len(ng2["testgate"].parameters), 2)
        self.assertEqual(len(ng1["testgate"].parameters), 1)

    def test_multiple_usepulses_other(self):
        """Test multiple usepulses statements (in the reverse order) cause the correct
        overwrite."""
        text = """
            from tests.core.gpf2 usepulses *
            from tests.core.gpf1 usepulses *
        """
        jc = parse_jaqal_string(text, autoload_pulses=True)
        from tests.core.gpf1 import NATIVE_GATES as ng1
        from tests.core.gpf2 import NATIVE_GATES as ng2

        self.assertIs(jc.native_gates["testgate"], ng1["testgate"])
        self.assertEqual(len(ng1["testgate"].parameters), 1)
        self.assertEqual(len(ng2["testgate"].parameters), 2)
