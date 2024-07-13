"""Dynamic item registry management for Python.

Registries helps applications manage registration, iteration, and lookup
of classes, objects, or other items. It's useful for applications that
offer extensibility, such as multiple backends for an abstract interface.

This is built using best practices developed as part of
`Review Board <https://www.reviewboard.org>`_, our code review and document
review product from `Beanbag <https://www.beanbaginc.com>`_.

The following forwarding imports are available directly through this module:

.. autosummary::
   :nosignatures:

   ~registries.registry.EntryPointRegistry
   ~registries.registry.OrderedRegistry
   ~registries.registry.Registry

Version Added:
    1.0
"""

from registries._version import (VERSION,
                                 __version__,
                                 __version_info__,
                                 get_package_version,
                                 get_version_string,
                                 is_release)
from registries.registry import (EntryPointRegistry,
                                 OrderedRegistry,
                                 Registry)


__all__ = [
    'EntryPointRegistry',
    'OrderedRegistry',
    'Registry',
    'VERSION',
    '__version__',
    '__version_info__',
    'get_package_version',
    'get_version_string',
    'is_release',
]


__autodoc_excludes__ = __all__
