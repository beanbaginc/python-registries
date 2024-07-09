"""Dynamic item registry management for Python.

Registries helps applications manage registration, iteration, and lookup
of classes, objects, or other items. It's useful for applications that
offer extensibility, such as multiple backends for an abstract interface.

This is built using best practices developed as part of
`Review Board <https://www.reviewboard.org>`_, our code review and document
review product from `Beanbag <https://www.beanbaginc.com>`_.

Version Added:
    1.0
"""

from registries._version import (VERSION,
                                 __version__,
                                 __version_info__,
                                 get_package_version,
                                 get_version_string,
                                 is_release)


__all__ = [
    'VERSION',
    '__version__',
    '__version_info__',
    'get_package_version',
    'get_version_string',
    'is_release',
]
