# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Define the infrastructure for visiting Jaqal core types"""

from jaqalpaq.error import JaqalError


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

    def __init__(self, *args, trace=None, **kwargs):
        self.started = trace is None
        self.trace = trace
        self.address = []
        super().__init__(*args, **kwargs)

    def trace_statements(self, statements):
        address = self.address
        if self.started:
            n = 0
            address.append(n)
        else:
            start = self.trace.start
            if start[: len(address)] != address:
                assert start[: len(address)] > address
                return
            n = start[len(address)]
            address.append(n)
            if start == address:
                self.started = True

        len_address = len(address)

        if self.trace and (address > self.trace.end):
            # This is the measure -> prepare case
            while n < len(statements):
                yield n, statements[n]
                assert len(address) == len_address
                n = address[-1] = n + 1
            n = address[-1] = 0

        while n < len(statements):
            yield n, statements[n]
            assert len(address) == len_address
            n = address[-1] = n + 1
            if self.trace and (address > self.trace.end):
                break
        address.pop()

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
