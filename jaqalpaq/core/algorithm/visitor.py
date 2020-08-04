# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Define the infrastructure for visiting Jaqal core types"""

from jaqalpaq import JaqalError


class Visitor:
    """Base class for all visitors for the Jaqal core types. To use this class, create a subclass and create methods
    named visit_<classname> for each class you wish to define behavior for. Then instantiate your visitor and call
    the visit method with the object you want to visit as the first argument. The appropriate method will automatically
    be called.

    For example::

        class GateVisitor(Visitor):
            def visit_GateStatement(self, gate):
                print(gate)

        visitor = GateVisitor()
        visitor.visit(gate)
    """

    def visit_default(self, obj, *args, **kwargs):
        """Method called when no method matches. Override to provide default behavior.

        :param object obj: The Jaqal core type object to visit.
        :raises JaqalError: Because this method should never be called unless overriden."""
        raise JaqalError(f"No visitor defined for {obj}")

    def visit(self, obj, *args, **kwargs):
        """Find the appropriate visitor method for the argument and call it.

        :param object obj: The Jaqal core type object to visit.
        :raises JaqalError: If there is no matching visitor method and the default visitor has not been overriden."""
        method_name = self._resolve_method_name(obj)
        return getattr(self, method_name)(obj, *args, **kwargs)

    def _resolve_method_name(self, obj):
        """Find a method to call by tracing the object's MRO. If no method is found in this visitor,
        return the default visitor."""
        for cls in type(obj).__mro__:
            method_name = f"visit_{cls.__name__}"
            if hasattr(self, method_name):
                return method_name
        return "visit_default"
