# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
__import__("pkg_resources").declare_namespace(__name__)

from .error import JaqalError
from .utilities import RESERVED_WORDS

# This variable controls whether to monkeypatch the sly library to
# remove some expensive checks. This has no side effects if the
# jaqalpaq parser is working correctly and sly has not changed. Set
# this to False before parsing any jaqal code if you are experiencing
# unexplained error messages or other issues with parsing.
_PARSER_SLY_TURBO = True
