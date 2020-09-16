import unittest
from itertools import dropwhile, takewhile
from abc import abstractmethod

from jaqalpaq.core import ParamType
from . import common
from .randomize import random_identifier, random_whole


class AbstractGateTesterBase:

    ##
    # Interface derived classes must adhere to
    #

    @abstractmethod
    def create_random_instance(self, **kwargs):
        pass

    @property
    @abstractmethod
    def tested_type(self):
        pass

    ##
    # Tests common to all AbstractGate types.
    #

    def test_create_gate_definition(self):
        """Create a new gate definition, ignoring its ideal action."""
        gatedef, name, params = self.create_random_instance(return_params=True)
        self.assertEqual(name, gatedef.name)
        self.assertEqual(params, gatedef.parameters)

    def test_instantiate_no_args(self):
        """Test creating a GateStatement from a GateDefinition with no arguments."""
        gatedef = self.create_random_instance(parameter_count=0)
        gate = gatedef()
        self.assertEqual({}, gate.parameters)
        self.assertEqual(gatedef.name, gate.name)
        gate = gatedef.call()
        self.assertEqual({}, gate.parameters)
        self.assertEqual(gatedef.name, gate.name)

    def test_positional_args(self):
        gatedef = self.create_random_instance()
        arg_types = [param.kind for param in gatedef.parameters]
        arguments = common.make_random_argument_list(arg_types)
        gate = gatedef(*arguments)
        arg_dict = {
            param.name: arg for param, arg in zip(gatedef.parameters, arguments)
        }
        self.assertEqual(arg_dict, gate.parameters)
        self.assertEqual(gatedef.name, gate.name)
        gate = gatedef.call(*arguments)
        self.assertEqual(arg_dict, gate.parameters)
        self.assertEqual(gatedef.name, gate.name)

    def test_fail_too_many_args(self):
        """Test creating a GateStatement from a GateDefinition with the wrong number of arguments."""
        gatedef = self.create_random_instance()
        arg_types = [param.kind for param in gatedef.parameters]
        arguments = common.make_random_argument_list(arg_types + [None])
        with self.assertRaises(Exception):
            gatedef(*arguments)
        with self.assertRaises(Exception):
            gatedef.call(*arguments)

    def test_fail_too_few_args(self):
        """Test creating a GateStatement from a GateDefinition with the wrong number of arguments."""
        gatedef = self.create_random_instance(parameter_count=random_whole())
        arg_types = [param.kind for param in gatedef.parameters]
        arguments = common.make_random_argument_list(arg_types[:-1])
        with self.assertRaises(Exception):
            gatedef(*arguments)
        with self.assertRaises(Exception):
            gatedef.call(*arguments)

    def test_fail_wrong_arg_type(self):
        """Test creating a GateStatement with the wrong argument types."""
        param_types = [ParamType.INT, ParamType.FLOAT, ParamType.QUBIT]
        for param_type in param_types:
            parameter = common.make_random_parameter(allowed_types=[param_type])
            gatedef = self.tested_type(random_identifier(), parameters=[parameter])
            other_types = [ptype for ptype in param_types if ptype != param_type]
            if param_type == ParamType.FLOAT:
                other_types.remove(ParamType.INT)
            for other_type in other_types:
                arguments = [common.make_random_value(other_type)]
                with self.assertRaises(Exception):
                    gatedef(*arguments)
                with self.assertRaises(Exception):
                    gatedef.call(*arguments)

    def test_instantiate_keyword_args(self):
        """Test instantiating a GateStatement using keyword arguments."""
        # Note: Jaqal doesn't use keyword arguments, but maybe another supported language does.
        gatedef = self.create_random_instance()
        arg_types = [param.kind for param in gatedef.parameters]
        arguments = common.make_random_argument_list(arg_types)
        kwargs = {param.name: arg for param, arg in zip(gatedef.parameters, arguments)}
        gate = gatedef(**kwargs)
        self.assertEqual(kwargs, gate.parameters)
        self.assertEqual(gatedef.name, gate.name)
        gate = gatedef.call(**kwargs)
        self.assertEqual(kwargs, gate.parameters)
        self.assertEqual(gatedef.name, gate.name)

    def test_fail_on_mixing_arg_types(self):
        """Test failing when mixing positional and keyword arguments."""
        gatedef = self.create_random_instance(parameter_count=random_whole(lower=2))
        arg_types = [param.kind for param in gatedef.parameters]
        arguments = common.make_random_argument_list(arg_types)
        arg_dict = {
            param.name: arg for param, arg in zip(gatedef.parameters, arguments)
        }
        args = [
            arg
            for _, arg in takewhile(
                lambda x: x[0] < len(arguments) // 2, enumerate(arguments)
            )
        ]
        kwargs = {
            key: value
            for _, (key, value) in dropwhile(
                lambda x: x[0] < len(arguments) // 2, enumerate(arg_dict.items())
            )
        }
        assert len(args) + len(kwargs) == len(arguments)
        with self.assertRaises(Exception):
            gatedef(*args, **kwargs)
        with self.assertRaises(Exception):
            gatedef.call(*args, **kwargs)

    def test_fail_too_few_keyword_args(self):
        """Test failing when not providing enough keyword arguments."""
        gatedef = self.create_random_instance(parameter_count=random_whole())
        arg_types = [param.kind for param in gatedef.parameters]
        arguments = common.make_random_argument_list(arg_types[:-1])
        kwargs = {param.name: arg for param, arg in zip(gatedef.parameters, arguments)}
        with self.assertRaises(Exception):
            gatedef(**kwargs)
        with self.assertRaises(Exception):
            gatedef.call(**kwargs)

    def test_fail_too_many_keyword_args(self):
        """Test failing when providing unnecessary keyword arguments."""
        gatedef = self.create_random_instance(parameter_count=random_whole())
        arg_types = [param.kind for param in gatedef.parameters]
        arguments = common.make_random_argument_list(arg_types + [None])
        kwargs = {param.name: arg for param, arg in zip(gatedef.parameters, arguments)}
        while True:
            new_name = random_identifier()
            if new_name not in kwargs:
                break
        kwargs[new_name] = arguments[-1]
        with self.assertRaises(Exception):
            gatedef(**kwargs)
        with self.assertRaises(Exception):
            gatedef.call(**kwargs)
