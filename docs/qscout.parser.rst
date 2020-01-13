qscout.parser package
=====================

..
	To avoid confusing the PLY library, which inspects docstrings to build a grammar, we
	cannot autodoc this module.

.. module:: qscout.parser

.. function:: qscout.parser.parse_jaqal_string(jaqal)
	
	Loads a Jaqal program into a :class:`ScheduledCircuit` object that represents it.
	
	:param str jaqal: The text of the Jaqal code to parse.
	:returns: The circuit it describes.
	:rtype: ScheduledCircuit