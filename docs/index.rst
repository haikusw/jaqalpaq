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
Jaqal-PUP currently consists of the :mod:`jaqal` Python package, and its seven subpackages.

* The :mod:`jaqal.core` package implements an object representation of scheduled quantum circuits. It supports programmatically constructing and manipulating circuits.
* The :mod:`jaqal.parser` package parses Jaqal source files into :mod:`jaqal.core` :class:`ScheduledCircuit` objects.
* The :mod:`jaqal.generator` package generates Jaqal code that implements the quantum circuit described by a :class:`ScheduledCircuit` object.
* The :mod:`jaqal.scheduler` package modifies circuits to execute more gates in parallel, without changing the function of the circuit or breaking the restrictions of the QSCOUT hardware.
* The :mod:`jaqal.cirq`, :mod:`jaqal.projectq`, :mod:`jaqal.qiskit`, :mod:`jaqal.quil`, and :mod:`jaqal.tket` packages allow conversion between :mod:`jaqal.core` objects and their counterparts in other popular quantum software development frameworks.

Additionally, the top-level :mod:`jaqal` package provides a few useful imports that don't fit
within the scope of any of the above subpackages: the :exc:`jaqal.QSCOUTError` class and a collection of :data:`RESERVED_WORDS`.


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
