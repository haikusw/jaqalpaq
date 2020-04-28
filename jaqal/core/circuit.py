from .block import BlockStatement, LoopStatement
from .constant import Constant
from .gate import GateStatement
from .gatedef import GateDefinition
from .macro import Macro
from .register import Register, NamedQubit
from .identifier import is_identifier_valid
from jaqal import RESERVED_WORDS, JaqalError
import re


class ScheduledCircuit:
    """
	Represents an entire quantum program.
	
	:param native_gates: Set these gates as the native gates to be used in this circuit. If not
	given, use the QSCOUT native gate set.
	:type native_gates: Optional[dict] or Optional[list]
	
	"""  # TODO: Flesh this out more, explain how it's used and how it maps to the structure of a Jaqal file.

    def __init__(self, native_gates=None):
        self._constants = {}
        self._macros = {}
        self._registers = {}
        self._native_gates = normalize_native_gates(native_gates)
        self._body = BlockStatement()

    def __repr__(self):
        return f"ScheduledCircuit(constants={self._constants}, macros={self._macros}, native_gates={self._native_gates}, registers={self._registers}, body={self._body})"

    def __eq__(self, other):
        try:
            return (
                self.constants == other.constants
                and self.macros == other.macros
                and self.native_gates == other.native_gates
                and self.registers == other.registers
                and self.body == other.body
            )
        except AttributeError:
            return False

    @property
    def constants(self):
        """Read-only access to a dictionary mapping names to :class:`Constant` objects,
		corresponding to ``let`` statements in the header of a Jaqal file."""
        return self._constants

    @property
    def macros(self):
        """Read-only access to a dictionary mapping names to :class:`Macro` objects,
		corresponding to ``macro`` statements in a Jaqal file."""
        return self._macros

    @property
    def native_gates(self):
        """Read-only access to a dictionary mapping names to :class:`GateDefinition`
		objects, corresponding to the contents of a gate definition file."""
        return self._native_gates

    @property
    def registers(self):
        """Read-only access to a dictionary mapping names to :class:`Register`
		objects, corresponding to ``reg`` and ``map`` statements in the header of a Jaqal
		file."""
        return self._registers

    @property
    def body(self):
        """Read-only access to a :class:`BlockStatement` object that contains the main body of
		the program."""
        return self._body

    def fundamental_registers(self):
        """
		:returns: all of the circuit's registers that correspond to ``reg`` statements, that is, all those that are not aliases for some other register.
		:rtype: list(Register)
		"""
        return [r for r in self.registers.values() if r.fundamental]

    def used_qubit_indices(self, instr=None, context={}):
        """
		:param instr: The instruction to query; defaults to the entire circuit.
		:type instr: BlockStatement or None
		:param context: If using this method to inspect an instruction in a macro call, provides information about the current scope. Unless you know precisely what you're doing, you should most likely omit this.
		:type context: dict
		:returns: A dict mapping fundamental register names to sets of the indices within those registers which are used by the instruction.
		"""
        if isinstance(instr, LoopStatement):
            return self.used_qubit_indices(instr.statements)

        indices = {r.name: set() for r in self.fundamental_registers()}
        if instr is None:
            instr = self.body

        if isinstance(instr, BlockStatement):
            for sub_instr in instr:
                new_indices = self.used_qubit_indices(sub_instr)
                for k in new_indices:
                    indices[k] |= new_indices[k]
        elif isinstance(instr, GateStatement):
            if instr.name in self.native_gates:
                for param_name in instr.parameters:
                    param = instr.parameters[param_name]
                    if isinstance(param, NamedQubit):
                        reg, idx = param.resolve_qubit(context)
                        indices[reg.name].add(idx)
                    elif isinstance(param, Register):
                        if param.size is not None:
                            size = param.size
                        else:
                            size = param.resolve_size()
                        for reg, idx in [
                            param[i].resolve_qubit(context) for i in range(size)
                        ]:
                            indices[reg.name].add(idx)
            elif instr.name in self.macros:
                return self.used_qubit_indices(
                    self.macros[instr.name].body, {**context, **instr.parameters}
                )
            else:
                raise JaqalError("Unknown gate %s." % instr.name)

        return indices

    def validate_identifier(self, name):
        """
		Tests whether a name is available to name a new constant, macro, or register in
		the circuit. Checks whether it's already used for a constant, macro, or register;
		whether it's one of the the native gates; whether it's a word reserved by the
		Jaqal language; and whether it fits the form of a Jaqal identifier (begins with a
		letter or underscore, all characters are alphanumeric or underscore).
		
		:param str name: The name to test.
		:returns: Whether the name is available.
		:rtype: bool
		"""
        if name in self.constants:
            return False
        if name in self.macros:
            return False
        if name in self.native_gates:
            return False
        if name in self.registers:
            return False
        return is_identifier_valid(name)

    def let(self, name, value):
        """
		Creates a new :class:`Constant`, mapping the given name to the given value, and adds it to
		the circuit. Equivalent to the Jaqal header statement :samp:`let {name} {value}`.
		
		:param str name: The name of the new constant.
		:param value: The numeric value of the new constant.
		:type value: int or float
		:returns: The new object.
		:rtype: Constant
		:raises JaqalError: if the name is not available (see :meth:`validate_identifier`).
		"""
        if self.validate_identifier(name):
            self.constants[name] = Constant(name, value)
            return self.constants[name]
        else:
            raise JaqalError("Name %s already used or invalid." % name)

    def reg(self, name, size):
        """
		Allocates a new fundamental :class:`Register` of the given size, adding it to the
		circuit under the given name. Equivalent to the Jaqal header statement
		:samp:`reg {name}[{size}]`.
		
		:param str name: The name of the register.
		:param int size: How many qubits are in the register.
		:returns: The new register.
		:rtype: Register
		:raises JaqalError: if there's already a register declared for this circuit, or
			if the name provided is not available (see :meth:`validate_identifier`).
		"""
        if self.validate_identifier(name):
            if self.registers:
                raise JaqalError("Only one reg statement per program is permitted.")
            self.registers[name] = Register(name, size)
            return self.registers[name]
        else:
            raise JaqalError("Name %s already used or invalid." % name)

    def map(self, name, source, idxs=None):
        """
		Creates a new :class:`Register` (or :class:`NamedQubit`, if idxs is a single index
		rather than a slice) mapped to some subset of an existing register, and adds it to
		the circuit. Equivalent to the Jaqal header statement
		:samp:`map {name} {source}[{idxs}]`.
		
		:param str name: The name of the new register.
		:param source: The source register to map the new register onto, or its name.
		:type source: Register or str
		:param idxs: Which qubits in the source register to map. If None, map the entire register.
		:type idxs: slice, int, AnnotatedValue, or None
		:returns: The new register.
		:rtype: Register or NamedQubit
		:raises JaqalError: if the name is invalid (see :meth:`validate_identifier`), or
			the source register isn't part of this circuit, or there's no register with
			the name provided for the source, or if the source register is a single qubit
			and ``idxs`` isn't ``None``, or if creating the :class:`Register` fails.
		"""
        if self.validate_identifier(name):
            if source is None:
                raise JaqalError("Map statement for %s must have a source." % name)
            else:
                if source in self.registers:
                    source_r = self.registers[source]
                elif (
                    source.name in self.registers
                    and self.registers[source.name] == source
                ):
                    source_r = source
                else:
                    raise JaqalError("Register %s does not exist." % source)
                if isinstance(source_r, NamedQubit):
                    if idxs is None:
                        self.registers[name] = source_r.renamed(name)
                    else:
                        raise JaqalError("Cannot index into single qubit %s." % source)
                else:
                    if idxs is None:
                        self.registers[name] = Register(name, alias_from=source_r)
                    elif isinstance(idxs, slice):
                        self.registers[name] = Register(
                            name, alias_from=source_r, alias_slice=idxs
                        )
                    else:
                        self.registers[name] = NamedQubit(name, source_r, idxs)
        else:
            raise JaqalError("Name %s already used or invalid." % name)
        return self.registers[name]

    def macro(self, name, parameters=None, body=None):
        """
		Defines a :class:`Macro` and adds it to the circuit. Equivalent to the Jaqal
		statement :samp:`macro {name} {parameters} \{{body}\}`.
		
		:param str name: The name of the macro.
		:param parameters: What arguments (numbers, qubits, etc) the macro should be
			called with. If None, the macro takes no parameters.
		:type parameters: list(Parameter) or None
		:param BlockStatement body: What statements the macro expands to when called.
		:returns: The new macro.
		:rtype: Macro
		:raises JaqalError: if the name of the macro or any of its parameters is invalid (see :meth:`validate_identifier`).
		"""
        if self.validate_identifier(name):
            if parameters is not None:
                for parameter in parameters:
                    if (
                        not self.validate_identifier(parameter.name)
                    ) or parameter.name == name:
                        raise JaqalError(
                            "Name %s already used or invalid." % parameter.name
                        )
            self.macros[name] = Macro(name, parameters, body)
            return self.macros[name]
        else:
            raise JaqalError("Name %s already used or invalid." % name)

    def build_gate(self, name, *args, **kwargs):
        """
		Creates a new :class:`GateStatement` object, but does not add it to the circuit.
		This is useful for constructing blocks and macros. More specifically, it looks up
		the name provided in the circuit's :attr:`native_gates` and :attr:`macros`, and
		if it finds an :class:`AbstractGate`, it calls its :meth:`call` method (the
		documentation for which explains in more detail what is done here).
		
		:param str name: The name of the gate to call.
		:returns: The new statement.
		:rtype: GateStatement
		:raises JaqalError: if the gate name doesn't match any native gate or macro, or
			if constructing the :class:`GateStatement` fails.
		"""
        if name in self.macros:
            return self.macros[name].call(*args, **kwargs)
        elif name in self.native_gates:
            return self.native_gates[name].call(*args, **kwargs)
        else:
            raise JaqalError("Unknown gate %s." % name)

    def gate(self, name, *args, **kwargs):
        """
		Creates a new :class:`GateStatement` object, and adds it immediately to the end of
		the circuit. More specifically, it looks up the name provided in the circuit's
		:attr:`native_gates` and :attr:`macros`, and if it finds an :class:`AbstractGate`,
		it calls its :meth:`call` method (the documentation for which explains in more
		detail what is done here). Equivalent to a gate statement in Jaqal.
		
		:param str name: The name of the gate to call.
		:returns: The new statement.
		:rtype: GateStatement
		:raises JaqalError: if the gate name doesn't match any native gate or macro, or
			if constructing the :class:`GateStatement` fails.
		"""
        g = self.build_gate(name, *args, **kwargs)
        self.body.append(g)
        return g

    def block(self, parallel=False, statements=None):
        """
		Creates a new :class:`BlockStatement` object, and adds it to the end of the circuit.
		All parameters are passed through to the :class:`BlockStatement` constructor.
		
		:param parallel: Set to False (default) for a sequential block, True for a
			parallel block, or None for an unscheduled block, which is treated as a
			sequential block except by the :mod:`jaqal.scheduler` submodule.
		:type parallel: bool or None
		:param statements: The contents of the block.
		:type statements: list(GateStatement, LoopStatement, BlockStatement)
		:returns: The new block.
		:rtype: BlockStatement
		"""
        b = BlockStatement(parallel, statements)
        self.body.append(b)
        return b

    def loop(self, iterations, statements=None, parallel=False):
        """
		Creates a new :class:`BlockStatement` object, and adds it to the end of the circuit.
		All parameters are passed through to the :class:`BlockStatement` constructor.
		
		:param int iterations: How many times to repeat the loop.
		:param statements: The contents of the loop. If a :class:`BlockStatement` is passed, it will
			be used as the loop's body; otherwise, a new :class:`BlockStatement` will be
			created with the list of instructions passed.
		:type statements: BlockStatement or list(GateStatement, LoopStatement, BlockStatement)
		:param parallel: If a new :class:`BlockStatement` is created, this will be passed to
			its constructor. Set to False (default) for a sequential block, True for a
			parallel block, or None for an unscheduled block, which is treated as a
			sequential block except by the :mod:`jaqal.scheduler` submodule.
		:type parallel: bool or None
		:returns: The new loop.
		:rtype: LoopStatement
		
		.. warning::
			If a :class:`BlockStatement` is passed for ``gates``, then ``parallel`` will be ignored!
		"""
        # Parallel is ignored if a BlockStatement is passed in; it's only used if building a BlockStatement at the same time as the LoopStatement.
        # This is intentional, but may or may not be wise.
        if isinstance(statements, BlockStatement):
            l = LoopStatement(iterations, statements)
        else:
            l = LoopStatement(iterations, BlockStatement(parallel, statements))
        self.body.append(l)
        return l


def normalize_native_gates(native_gates):
    """Takes in the different ways that native gates can be represented and
	returns a dictionary.

	:param native_gates: A list or dict of gates, or None.
	:type native_gates: Optional[dict] or Optional[list]
	"""
    native_gates = native_gates or {}
    if not isinstance(native_gates, dict):
        # This covers all iterables like list and tuple
        native_gates = {gate.name: gate for gate in native_gates}
    if any(name != gate.name for name, gate in native_gates.items()):
        raise ValueError(f"Native gate dictionary key did not match its name")
    if any(not isinstance(gate, GateDefinition) for gate in native_gates.values()):
        raise TypeError("Native gates must be GateDefinition instances")
    return native_gates
