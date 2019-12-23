.. Jaqal-PUP documentation master file, created by
   sphinx-quickstart on Fri Dec 20 16:22:58 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Jaqal Programming Utilities Project (Jaqal-PUP)
===============================================

API Reference
-------------
Jaqal-PUP currently consists of the :mod:`qscout` Python package, and its seven subpackages.

* The :mod:`qscout.core` package implements an object representation of scheduled quantum circuits. It supports programmatically constructing and manipulating circuits.
* The :mod:`qscout.parser` package parses Jaqal source files into :mod:`qscout.core` :class:`ScheduledCircuit` objects.
* The :mod:`qscout.generator` package generates Jaqal code that implements the quantum circuit described by a :class:`ScheduledCircuit` object.
* The :mod:`qscout.scheduler` package modifies circuits to execute more gates in parallel, without changing the function of the circuit or breaking the restrictions of the QSCOUT hardware.
* The :mod:`qscout.cirq`, :mod:`qscout.qiskit`, and :mod:`qscout.quil` packages allow conversion between :mod:`qscout.core` objects and their counterparts in other popular quantum software development frameworks.

Additionally, the top-level :mod:`qscout` package provides a few useful imports that don't fit
within the scope of any of the above subpackages: the :exc:`qscout.QSCOUTError` class and a collection of :data:`RESERVED_WORDS`.


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
