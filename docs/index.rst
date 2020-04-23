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
Jaqal-PUP currently consists of the :mod:`jaqalpup` Python package, and its subpackages:

* The :mod:`jaqalpup.core` package implements an object representation of scheduled quantum circuits. It supports programmatically constructing and manipulating circuits.
* The :mod:`jaqalpup.parser` package parses Jaqal source files into :mod:`jaqalpup.core` :class:`ScheduledCircuit` objects.
* The :mod:`jaqalpup.generator` package generates Jaqal code that implements the quantum circuit described by a :class:`ScheduledCircuit` object.
* The :mod:`jaqalpup.scheduler` package modifies circuits to execute more gates in parallel, without changing the function of the circuit or breaking the restrictions of the QSCOUT hardware.

Additionally, the top-level :mod:`jaqalpup` package provides a few useful imports that don't fit
within the scope of any of the above subpackages: the :exc:`jaqalpup.QSCOUTError` class and a collection of :data:`RESERVED_WORDS`.


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
