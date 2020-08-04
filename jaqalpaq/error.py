# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
class JaqalError(Exception):
    """Base class for errors raised as a result of failures to comply with the Jaqal specification, trying to use features not supported by the native hardware, or trying to convert quantum circuits that don't currently have Jaqal equivalents."""

    pass
