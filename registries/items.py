"""Types for items.

Version Added:
    1.0
"""

from __future__ import annotations

from typing import TypeVar


#: A generic type for items stored in a registry.
#:
#: This can be used for subclasses of :py:class:`Registry`, mixins, or other
#: utility code that need to stay generic. In normal usage, an explicit type
#: will be provided when subclassing instead.
#:
#: Version Added:
#:     1.0
RegistryItemType = TypeVar('RegistryItemType')
