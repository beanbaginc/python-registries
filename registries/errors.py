"""Registry error classes.

Version Added:
    1.0
"""

from __future__ import annotations

from typing import Any, ClassVar, Generic, Optional, TYPE_CHECKING
from typing_extensions import Protocol

from registries.items import RegistryItemType

try:
    from enum import StrEnum
except ImportError:
    assert not TYPE_CHECKING

    from enum import Enum

    class StrEnum(str, Enum):  # type: ignore
        pass

if TYPE_CHECKING:
    class _FormatStr(Protocol):
        def __mod__(
            self,
            x: Any,
            /
        ) -> str:
            ...


class BaseRegistryError(Exception):
    """Base class for a registry exception.

    Version Added:
        1.0
    """

    #: The template for an error message.
    #:
    #: This is in the form of a ``%``-based format string. Subclasses can
    #: provide custom error messages for specific error types or custom
    #: registries.
    message_template: ClassVar[_FormatStr] = (
        "Unspecified registry error. This is an implementation error with "
        "the application's custom registry error handling."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize the error.

        Args:
            message (str, optional):
                An explicit error message as a ``%``-based format string.

                If not provided, :py:attr:`message_template` will be used.
        """
        super().__init__((message or self.message_template) % kwargs)


class UnsupportedRegistryAttributeError(BaseRegistryError):
    """An attribute was referenced that is not supported by the registry.

    Version Added:
        1.0
    """

    message_template = (
        '"%(attr_name)s" is not a registered lookup attribute.'
    )

    ######################
    # Instance variables #
    ######################

    #: The name of the unsupported attribute that was used.
    attr_name: str

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        attr_name: str,
        **kwargs,
    ) -> None:
        """Initialize the error.

        Args:
            attr_name (str):
                The name of the unsupported attribute that was used.

            message (str, optional):
                An explicit error message as a ``%``-based format string.

                This support an ``%(attr_name)s`` format argument.

                If not provided, :py:attr:`message_template` will be used.
        """
        super().__init__(message=message,
                         attr_name=attr_name,
                         **kwargs)

        self.attr_name = attr_name


class BaseRegistryItemLookupError(BaseRegistryError):
    """Base class for errors in looking up an item from a registry.

    Version Added:
        1.0
    """

    ######################
    # Instance variables #
    ######################

    #: The name of the attribute that was used to look up the item.
    attr_name: str

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        attr_name: str,
        **kwargs,
    ) -> None:
        """Initialize the error.

        Args:
            attr_name (str):
                The name of the attribute that was used to look up the item.

            message (str, optional):
                An explicit error message as a ``%``-based format string.

                This support an ``%(attr_name)s`` format argument.

                If not provided, :py:attr:`message_template` will be used.
        """
        super().__init__(message=message,
                         attr_name=attr_name,
                         **kwargs)

        self.attr_name = attr_name


class ItemNotFoundLookupError(BaseRegistryItemLookupError):
    """An item could not be found in the registry.

    Version Added:
        1.0
    """

    message_template = (
        'No item registered with %(attr_name)s=%(attr_value)s.'
    )

    ######################
    # Instance variables #
    ######################

    #: The attribute value used to look up the item.
    attr_value: object

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        attr_name: str,
        attr_value: object,
    ) -> None:
        """Initialize the error.

        Args:
            attr_name (str):
                The name of the attribute that was used to look up the item.

            attr_value (object):
                The attribute value used to look up the item.

            message (str, optional):
                An explicit error message as a ``%``-based format string.

                This supports ``%(attr_name)s`` and ``%(attr_value)s`` format
                arguments.

                If not provided, :py:attr:`message_template` will be used.
        """
        super().__init__(message=message,
                         attr_name=attr_name,
                         attr_value=attr_value)

        self.attr_value = attr_value


class BaseRegistrationError(Generic[RegistryItemType],
                            BaseRegistryError):
    """Base class for registration errors.

    Version Added:
        1.0
    """

    ######################
    # Instance variables #
    ######################

    #: The item that failed to be registered.
    item: RegistryItemType

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        item: RegistryItemType,
        **kwargs,
    ) -> None:
        """Initialize the error.

        Args:
            item (object):
                The item that failed to be registered.

            message (str, optional):
                An explicit error message as a ``%``-based format string.

                This supports an ``%(item)s`` format argument.

                If not provided, :py:attr:`message_template` will be used.
        """
        super().__init__(message=message,
                         item=item,
                         **kwargs)

        self.item = item


class AlreadyRegisteredError(BaseRegistrationError[RegistryItemType]):
    """The provided item is already registered.

    Version Added:
        1.0
    """

    message_template = (
        'Could not register %(item)s: it is already registered.'
    )


class RegistrationConflictError(BaseRegistrationError[RegistryItemType]):
    """The provided item conflicts with an item that is already registered.

    This may apply to a separate item matching the same lookup attributes.

    Version Added:
        1.0
    """

    message_template = (
        'Could not register %(item)s: another item (%(other_item)s) is '
        'already registered with %(attr_name)s=%(attr_value)s.'
    )

    ######################
    # Instance variables #
    ######################

    #: The name of the attribute that was used for registration.
    attr_name: str

    #: The attribute value that conflicted.
    attr_value: object

    #: The conflicting item already in the registry.
    other_item: RegistryItemType

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        attr_name: str,
        attr_value: Any,
        item: RegistryItemType,
        other_item: RegistryItemType,
    ) -> None:
        """Initialize the error.

        Args:
            attr_name (str):
                The name of the attribute that was used for registration.

            attr_value (object):
                The attribute value that conflicted.

            item (object):
                The item that failed to be registered.

            other_item (object):
                The conflicting item already in the registry.

            message (str, optional):
                An explicit error message as a ``%``-based format string.

                This supports ``%(attr_name)s``, ``%(attr_value)s``,
                ``%(item)s``, and ``%(other_item)s`` format arguments.

                If not provided, :py:attr:`message_template` will be used.
        """
        super().__init__(message=message,
                         attr_name=attr_name,
                         attr_value=attr_value,
                         item=item,
                         other_item=other_item)

        self.attr_name = attr_name
        self.attr_value = attr_value
        self.other_item = other_item


class InvalidItemRegistrationError(BaseRegistrationError[RegistryItemType]):
    """An item could not be registered due to missing attributes.

    Version Added:
        1.0
    """

    message_template = (
        'Could not register %(item)s: it does not have a "%(attr_name)s" '
        'attribute.'
    )

    ######################
    # Instance variables #
    ######################

    #: The name of the attribute that was used for registration.
    attr_name: str

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        attr_name: str,
        item: RegistryItemType,
    ) -> None:
        """Initialize the error.

        Args:
            attr_name (str):
                The name of the attribute that was used for registration.

            item (object):
                The item that failed to be registered.

            message (str, optional):
                An explicit error message as a ``%``-based format string.

                This supports ``%(attr_name)s`` and ``%(item)s`` format
                arguments.

                If not provided, :py:attr:`message_template` will be used.
        """
        super().__init__(message=message,
                         item=item,
                         attr_name=attr_name)

        self.attr_name = attr_name


class BaseUnregistrationError(BaseRegistryError):
    """Base class for unregistration errors.

    Version Added:
        1.0
    """


class AttrNotFoundUnregistrationError(BaseUnregistrationError):
    """An item was not found by attribute for unregistration.

    Version Added:
        1.0
    """

    message_template = (
        'No item registered with %(attr_name)s=%(attr_value)s.'
    )

    ######################
    # Instance variables #
    ######################

    #: The name of the attribute that was used for unregistration.
    attr_name: str

    #: The attribute value that was used for the lookup.
    attr_value: object

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        attr_name: str,
        attr_value: object,
    ) -> None:
        """Initialize the error.

        Args:
            attr_name (str):
                The name of the attribute that was used for unregistration.

            attr_value (object):
                The attribute value that was used for the lookup.

            message (str, optional):
                An explicit error message as a ``%``-based format string.

                This supports ``%(attr_name)s`` and ``%(attr_value)s`` format
                arguments.

                If not provided, :py:attr:`message_template` will be used.
        """
        super().__init__(message=message,
                         attr_name=attr_name,
                         attr_value=attr_value)

        self.attr_name = attr_name
        self.attr_value = attr_value


class ItemNotFoundUnregistrationError(Generic[RegistryItemType],
                                      BaseUnregistrationError):
    """An item was not found for unregistration.

    Version Added:
        1.0
    """

    message_template = (
        'Could not unregister %(item)s: it is not registered.'
    )

    ######################
    # Instance variables #
    ######################

    #: The item that failed to be registered.
    item: RegistryItemType

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        item: RegistryItemType,
    ) -> None:
        """Initialize the error.

        Args:
            item (object):
                The item that failed to be unregistered.

            message (str, optional):
                An explicit error message as a ``%``-based format string.

                This supports an ``%(item)s`` format argument.

                If not provided, :py:attr:`message_template` will be used.
        """
        super().__init__(message=message,
                         item=item)

        self.item = item
