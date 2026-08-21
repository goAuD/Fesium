"""Single source of truth for the Fesium version.

Kept in its own module for two reasons: the root ``fesium.py`` launcher can
read it without executing the package ``__init__``, and setuptools can parse
the literal statically for ``project.version``.
"""

__version__ = "2.0.0"
