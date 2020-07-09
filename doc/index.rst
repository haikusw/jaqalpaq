.. toctree::
   :maxdepth: 2
   :caption: Contents:

Python Jaqal Programming Package (JaqalPaq)
===========================================

API Reference
-------------
JaqalPaq currently consists of the :mod:`jaqalpaq` Python package, and its subpackages:

* The :mod:`jaqalpaq.core` package implements an object representation of scheduled
  quantum circuits. It supports programmatically constructing and manipulating circuits.
* The :mod:`jaqalpaq.parser` package parses Jaqal source files into :mod:`jaqalpaq.core`
  :class:`Circuit` objects.
* The :mod:`jaqalpaq.generator` package generates Jaqal code that implements the
  quantum circuit described by a :class:`Circuit` object.
* The :mod:`jaqalpaq.emulator` package provides noiseless emulation of Jaqal code.

Additionally, the top-level :mod:`jaqalpaq` package provides a few useful imports that
don't fit within the scope of any of the above subpackages: the :exc:`jaqalpaq.JaqalError`
class and a collection of :data:`RESERVED_WORDS`.


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
* :ref:`glossary`
