class QSCOUTError(Exception):
	"""Base class for errors raised as a result of failures to comply with the Jaqal specification, trying to use features not supported by the QSCOUT hardware, or trying to convert quantum circuits that don't currently have Jaqal equivalents."""
	pass
