# The main, recommended way to access the parser is using the Interface class.
from .interface import Interface

# The following classes are used to read and manipulate parse trees without direct knowledge
# of their data type. The methods of TreeManipulators may be used directly or it may be subclassed.
# TreeRewriteVisitor should be subclassed and the appropriate methods overridden. Use the
# methods of TreeManipulators to extract useful information from the input arguments and reconstruct
# the trees.
from .parse import TreeManipulators, TreeRewriteVisitor
