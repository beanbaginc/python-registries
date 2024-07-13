"""Definitions of registries.

Registries are collections that keep track of unique objects. There are
three types provided by default:

1. :py:class:`Registry`: The main class for defining a registry.
2. :py:class:`EntryPointRegistry`: A registry backed by Python Entrypoints.
3. :py:class:`OrderedRegistry`: A registry that tracks the order of items.

All registries are thread-safe, extensible via hooks, and provide type hints.

Version Added:
    1.0
"""

from __future__ import annotations

import logging
import sys
from enum import Enum
from threading import RLock
from typing import (ClassVar, Generic, Iterable, Iterator, Optional,
                    Sequence, cast)

from registries.errors import (AlreadyRegisteredError,
                               AttrNotFoundUnregistrationError,
                               BaseRegistryItemLookupError,
                               InvalidItemRegistrationError,
                               ItemNotFoundLookupError,
                               ItemNotFoundUnregistrationError,
                               RegistrationConflictError,
                               UnsupportedRegistryAttributeError)

from registries.items import RegistryItemType

if sys.version_info[:2] >= (3, 12):
    from importlib.metadata import EntryPoint, entry_points
else:
    from importlib_metadata import EntryPoint, entry_points  # type: ignore


logger = logging.getLogger(__name__)


class RegistryState(Enum):
    """The operations state of a registry.

    Version Added:
        1.0
    """

    #: The registry is pending setup.
    PENDING = 0

    #: The registry is in the process of populating default items.
    POPULATING = 1

    #: The registry is populated and ready to be used.
    READY = 2


class Registry(Generic[RegistryItemType]):
    """An item registry.

    Item registries hold a set of objects that can be looked up by attributes.
    Each item is guaranteed to be unique and not share these attributes with
    any other item in the registry.

    Registries default to holding arbitrary objects. To limit objects to a
    specific type, specify a type when subclassing. For example:

    .. code-block:: python

        class MyRegistry(Registry[MyItemType]):
            ...

    Version Added:
        1.0
    """

    #: A list of attributes that items can be looked up by.
    lookup_attrs: Sequence[str] = []

    #: Error used when trying to register an already-registered item.
    #:
    #: Consumers can reference this attribute when catching exceptions.
    #:
    #: Subclasses can override this with a subclass of
    #: :py:class:`~registries.errors.AlreadyRegisteredError` to provide
    #: custom error messages.
    already_registered_error_cls: \
        type[AlreadyRegisteredError[RegistryItemType]] = \
        AlreadyRegisteredError[RegistryItemType]

    #: Error used when failing to unregister by attribute.
    #:
    #: Consumers can reference this attribute when catching exceptions.
    #:
    #: Subclasses can override this with a subclass of
    #: :py:class:`~registries.errors.UnregistrationAttrNotFoundError` to
    #: provide custom error messages.
    attr_not_found_unregistration_error_cls: \
        type[AttrNotFoundUnregistrationError] = \
        AttrNotFoundUnregistrationError

    #: Error used when failing to register an invalid item.
    #:
    #: Consumers can reference this attribute when catching exceptions.
    #:
    #: Subclasses can override this with a subclass of
    #: :py:class:`~registries.errors.InvalidItemRegistrationError` to provide
    #: custom error messages.
    invalid_item_registration_error_cls: \
        type[InvalidItemRegistrationError[RegistryItemType]] = \
        InvalidItemRegistrationError[RegistryItemType]

    #: Error used when failing to look up an unregistered item.
    #:
    #: Consumers can reference this attribute when catching exceptions.
    #:
    #: Subclasses can override this with a subclass of
    #: :py:class:`~registries.errors.ItemNotFoundLookupError` to provide
    #: custom error messages.
    item_not_found_lookup_error_cls: \
        type[ItemNotFoundLookupError] = \
        ItemNotFoundLookupError

    #: Error used when failing to unregister by item.
    #:
    #: Consumers can reference this attribute when catching exceptions.
    #:
    #: Subclasses can override this with a subclass of
    #: :py:class:`~registries.errors.UnregistrationItemNotFoundError` to
    #: provide #: custom error messages.
    item_not_found_unregistration_error_cls: \
        type[ItemNotFoundUnregistrationError[RegistryItemType]] = \
        ItemNotFoundUnregistrationError[RegistryItemType]

    #: Error used when failing to register a conflicting item.
    #:
    #: Consumers can reference this attribute when catching exceptions.
    #:
    #: Subclasses can override this with a subclass of
    #: :py:class:`~registries.errors.RegistrationConflictError` to provide
    #: custom error messages.
    registration_conflict_error_cls: \
        type[RegistrationConflictError[RegistryItemType]] = \
        RegistrationConflictError[RegistryItemType]

    #: Error used when referencing invalid attribute names.
    #:
    #: Consumers can reference this attribute when catching exceptions.
    #:
    #: Subclasses can override this with a subclass of
    #: :py:class:`~registries.errors.UnsupportedRegistryAttributeError` to
    #: provide custom error messages.
    unsupported_registry_attr_error_cls: \
        type[UnsupportedRegistryAttributeError] = \
        UnsupportedRegistryAttributeError

    ######################
    # Instance variables #
    ######################

    #: The current state of the registry.
    state: RegistryState

    #: A set of the items stored in the registry.
    _items: set[RegistryItemType]

    #: A lock used to ensure population only happens once.
    _lock: RLock

    #: The registry of stored items.
    #:
    #: This is a mapping of lookup attribute names to value-to-item mappings.
    _registry: dict[str, dict[object, RegistryItemType]]

    def __init__(self) -> None:
        """Initialize the registry."""
        self.state = RegistryState.PENDING

        self._registry = {
            _attr_name: {}
            for _attr_name in self.lookup_attrs
        }
        self._lock = RLock()
        self._items = set()

    def get(
        self,
        *attr_args,
        **attr_kwargs,
    ) -> RegistryItemType:
        """Return an item by its attribute value.

        Args:
            *attr_args (tuple):
                A single positional value for the query.

                This may be provided instead of ``attr_kwargs`` if the
                registry supports only a single lookup attribute. In this
                case, exactly one argument may be supplied.

            **query_kwarga (dict):
                An attribute/value query for an item.
                The query used to look up the provided item.

                This must contain exactly one key/value pair.

                This may be provided instead of ``attr_args`` to look up
                an object using an attribute/value match. In this case,
                exactly one argument may be supplied.

        Returns:
            object:
            The registered item.

        Raises:
            TypeError:
                The query arguments were invalid.

                A wrong combination of positional and keyword arguments
                were provided, or a wrong number of arguments.

                This class is the standard class used for invalid or missing
                function arguments.

            registries.errors.ItemNotFoundLookupError:
                An item matching the lookup attribute and value was not
                found.

            registries.errors.UnsupportedRegistryAttributeError:
                The provided lookup attribute is not supported on this type
                of registry.
        """
        attr_name, attr_value = self._get_query_attr(
            func_name='get',
            attr_args=attr_args,
            attr_kwargs=attr_kwargs)

        self.populate()

        try:
            attr_map = self._registry[attr_name]
        except KeyError:
            raise self.unsupported_registry_attr_error_cls(
                attr_name=attr_name)

        try:
            return attr_map[attr_value]
        except KeyError:
            raise self.item_not_found_lookup_error_cls(
                attr_name=attr_name,
                attr_value=attr_value)

    def get_or_none(
        self,
        *attr_args,
        **attr_kwargs,
    ) -> Optional[RegistryItemType]:
        """Return the requested registered item, or None if not found.

        Args:
            *attr_args (tuple):
                A single positional value for the query.

                This may be provided instead of ``attr_kwargs`` if the
                registry supports only a single lookup attribute. In this
                case, exactly one argument may be supplied.

            **query_kwarga (dict):
                An attribute/value query for an item.
                The query used to look up the provided item.

                This must contain exactly one key/value pair.

                This may be provided instead of ``attr_args`` to look up
                an object using an attribute/value match. In this case,
                exactly one argument may be supplied.

        Returns:
            object:
            The matching registered item, if found. Otherwise, ``None`` is
            returned.

        Raises:
            TypeError:
                The query arguments were invalid.

                A wrong combination of positional and keyword arguments
                were provided, or a wrong number of arguments.

                This class is the standard class used for invalid or missing
                function arguments.

            registries.errors.UnsupportedRegistryAttributeError:
                The provided lookup attribute is not supported on this type
                of registry.
        """
        attr_name, attr_value = self._get_query_attr(
            func_name='get_or_none',
            attr_args=attr_args,
            attr_kwargs=attr_kwargs)

        try:
            return self.get(**{
                attr_name: attr_value,
            })
        except BaseRegistryItemLookupError:
            return None

    def register(
        self,
        item: RegistryItemType,
    ) -> None:
        """Register an item.

        Args:
            item (object):
                The item to register with the class.

        Raises:
            registries.errors.AlreadyRegisteredError:
                This item was already registered.

            registries.errors.BaseRegistrationError:
                General exception used for any registration errors.

            registries.errors.InvalidItemRegistrationError:
                The item is missing a required lookup attribute.

            registries.errors.RegistrationConflictError:
                Another item with the same lookup attributes was already
                registered.
        """
        self.populate()
        attr_values: dict[str, object] = {}

        with self._lock:
            if item in self._items:
                raise self.already_registered_error_cls(item=item)

            self.on_item_registering(item)

            registry_map = self._registry

            for attr_name in self.lookup_attrs:
                attr_map = registry_map[attr_name]

                try:
                    attr_value = getattr(item, attr_name)

                    if attr_value in attr_map:
                        raise self.registration_conflict_error_cls(
                            item=item,
                            other_item=attr_map[attr_value],
                            attr_name=attr_name,
                            attr_value=attr_value)

                    attr_values[attr_name] = attr_value
                except AttributeError:
                    raise self.invalid_item_registration_error_cls(
                        attr_name=attr_name,
                        item=item)

            for attr_name, attr_value in attr_values.items():
                registry_map[attr_name][attr_value] = item

            self._items.add(item)
            self.on_item_registered(item)

    def unregister_by_attr(
        self,
        *attr_args,
        **attr_kwargs,
    ) -> None:
        """Unregister an item from the registry by an attribute.

        Args:
            **attr_args (tuple):
                A single positional value for the query.

                This may be provided instead of ``attr_kwargs`` if the
                registry supports only a single lookup attribute. In this
                case, exactly one argument may be supplied.

            **query_kwarga (dict):
                An attribute/value query for an item.
                The query used to look up the provided item.

                This must contain exactly one key/value pair.

                This may be provided instead of ``attr_args`` to look up
                an object using an attribute/value match. In this case,
                exactly one argument may be supplied.

        Raises:
            registries.errors.AttrNotFoundUnregistrationError:
                An item matching the lookup attribute was not found.

            registries.errors.BaseUnregistrationError:
                General exception used for any unregistration errors.

            registries.errors.UnsupportedRegistryAttributeError:
                The provided lookup attribute is not supported on this type
                of registry.
        """
        attr_name, attr_value = self._get_query_attr(
            func_name='unregister_by_attr',
            attr_args=attr_args,
            attr_kwargs=attr_kwargs)

        self.populate()

        with self._lock:
            try:
                attr_map = self._registry[attr_name]
            except KeyError:
                raise self.unsupported_registry_attr_error_cls(
                    attr_name=attr_name)

            try:
                item = attr_map[attr_value]
            except KeyError:
                raise self.attr_not_found_unregistration_error_cls(
                    attr_name=attr_name,
                    attr_value=attr_value)

            self.unregister(item)

    def unregister(
        self,
        item: RegistryItemType,
    ) -> None:
        """Unregister an item from the registry.

        Args:
            item (object):
                The item to unregister.

                This must be present in the registry.

        Raises:
            registries.errors.BaseUnregistrationError:
                General exception used for any unregistration errors.

            registries.errors.ItemNotFoundUnregistrationError:
                The item was not registered.
        """
        self.populate()

        with self._lock:
            self.on_item_unregistering(item)

            try:
                self._items.remove(item)
            except KeyError:
                raise self.item_not_found_unregistration_error_cls(
                    item=item)

            registry_map = self._registry

            for attr_name in self.lookup_attrs:
                attr_value = getattr(item, attr_name)
                del registry_map[attr_name][attr_value]

            self.on_item_unregistered(item)

    def populate(self) -> None:
        """Ensure the registry is populated.

        Calling this method when the registry is populated will have no effect.
        """
        if self.state == RegistryState.READY:
            return

        with self._lock:
            if self.state != RegistryState.PENDING:
                # This thread is actively populating the registry, or has been
                # populated while waiting for the lock to be released. We can
                # bail here.
                return

            self.state = RegistryState.POPULATING
            self.on_populating()

            for item in self.get_defaults():
                self.register(item)

            self.state = RegistryState.READY
            self.on_populated()

    def get_defaults(self) -> Iterable[RegistryItemType]:
        """Return the default items for the registry.

        This method should be overridden by a subclass.

        It may be return an explicit list or yield items one-by-one.

        Returns:
            list:
            The default items for the registry.
        """
        return []

    def reset(self) -> None:
        """Unregister all items and mark the registry unpopulated.

        This will result in the registry containing no entries. Any call to a
        method that would populate the registry will repopulate it.
        """
        with self._lock:
            if self.state == RegistryState.READY:
                self.on_resetting()

                for item in self._items.copy():
                    self.unregister(item)

                assert len(self._items) == 0

                self.on_reset()
                self.state = RegistryState.PENDING

    def on_item_registering(
        self,
        item: RegistryItemType,
        /,
    ) -> None:
        """Handle extra steps before registering an item.

        This can be used by subclasses to perform preparation steps before
        registering an item. It's run before the item is validated and then
        registered.

        Validation can be performed in this method.

        The method is thread-safe.

        Args:
            item (object):
                The item to register.

        Raises:
            registries.errors.BaseRegistrationError:
                There's an error registering this item.
        """
        pass

    def on_item_registered(
        self,
        item: RegistryItemType,
        /,
    ) -> None:
        """Handle extra steps after registering an item.

        This can be used by subclasses to perform additional steps when an
        item is registered. It's run after the main registration occurs.

        The method is thread-safe.

        Args:
            item (object):
                The item that was registered.
        """
        pass

    def on_item_unregistering(
        self,
        item: RegistryItemType,
        /,
    ) -> None:
        """Handle extra steps before unregistering an item.

        This can be used by subclasses to perform additional steps before
        validating and unregistering an item.

        The method is thread-safe.

        Args:
            item (object):
                The item to unregister.

        Raises:
            registries.errors.BaseUnregistrationError:
                There's an error unregistering this item.
        """
        pass

    def on_item_unregistered(
        self,
        item: RegistryItemType,
        /,
    ) -> None:
        """Handle extra steps after unregistering an item.

        This can be used by subclasses to perform additional steps when an
        item is unregistered. It's run after the main unregistration occurs.

        The method is thread-safe.

        Args:
            item (object):
                The item that was unregistered.
        """
        pass

    def on_populating(self) -> None:
        """Handle extra steps before a registry is populated.

        This can be used by subclasses to perform additional steps before the
        registry is populated.

        The method is thread-safe.
        """
        pass

    def on_populated(self) -> None:
        """Handle extra steps after a registry is populated.

        This can be used by subclasses to perform additional steps after the
        registry is populated. It's run after the main population occurs.

        The method is thread-safe.
        """
        pass

    def on_resetting(self) -> None:
        """Handle extra steps before resetting the registry.

        This can be used by subclasses to perform additional steps before the
        registry is reset. It's run before the main reset operations occur.

        The method is thread-safe.
        """
        pass

    def on_reset(self) -> None:
        """Handle extra steps after a registry is reset.

        This can be used by subclasses to perform additional steps after the
        registry is reset. It's run after the main reset operations occur.

        The method is thread-safe.
        """
        pass

    def _get_query_attr(
        self,
        *,
        func_name: str,
        attr_args: tuple[object, ...],
        attr_kwargs: dict[str, object],
    ) -> tuple[str, object]:
        """Return an attribute name and value used to look up an item.

        Args:
            func_name (str):
                The name of the function calling this method.

                This is used for error information.

            attr_args (tuple):
                The positional arguments query to inspect.

            attr_kwargs (dict):
                The keyword arguments query to inspect.

        Returns:
            tuple:
            A 2-tuple in the form of:

            Tuple:
                0 (str):
                    The attribute lookup name.

                1 (object):
                    The attribute lookup value.

        Raises:
            TypeError:
                The query arguments were invalid.

                A wrong combination of positional and keyword arguments
                were provided, or a wrong number of arguments.

                This class is the standard class used for invalid or missing
                function arguments.
        """
        if len(attr_args) == 1 and not attr_kwargs:
            if len(self.lookup_attrs) == 1:
                return self.lookup_attrs[0], attr_args[0]

            raise TypeError(
                'Positional arguments cannot be provided to %s.%s(). '
                'This registry only supports looking up items using '
                'keyword arguments.'
                % (type(self).__name__, func_name)
            )
        elif len(attr_kwargs) == 1 and not attr_args:
            return list(attr_kwargs.items())[0]

        raise TypeError(
            'Either one positional argument or one keyword argument '
            'may be provided to %s.%s().'
            % (type(self).__name__, func_name)
        )

    def __iter__(self) -> Iterator[RegistryItemType]:
        """Iterate through all items in the registry.

        This method does not provide a stable ordering.

        Yields:
            object:
            The items registered in this registry.
        """
        self.populate()

        yield from self._items

    def __len__(self) -> int:
        """Return the number of items in the registry.

        Returns:
            int:
            The number of items in the registry.
        """
        self.populate()

        return len(self._items)

    def __contains__(
        self,
        item: RegistryItemType,
    ) -> bool:
        """Return whether or not the item is contained in the registry.

        Args:
            item (object):
                The item to look for.

        Returns:
            bool:
            Whether or not the item is contained in the registry.
        """
        self.populate()

        return item in self._items


class EntryPointRegistry(Registry[RegistryItemType]):
    """A registry that auto-populates from an entry-point."""

    #: The entry point group name.
    entry_point_group: ClassVar[str]

    def __init__(self) -> None:
        """Initialize the registry."""
        assert hasattr(self, 'entry_point_group')

        super().__init__()

    def get_defaults(self) -> Iterable[RegistryItemType]:
        """Yield the values from the entry point.

        Yields:
            object:
            The object from the entry point.
        """
        eps = entry_points(group=self.entry_point_group)

        for ep in eps:
            try:
                yield self.process_value_from_entry_point(ep)
            except Exception as e:
                logger.exception('Could not load entry point "%s" for '
                                 'registry %s: %s.',
                                 ep.name, type(self).__name__, e)

    def process_value_from_entry_point(
        self,
        entry_point: EntryPoint,
    ) -> RegistryItemType:
        """Return the item to register from the entry point.

        By default, this returns the loaded entry point. Subclasses can
        override this to return a more explicit result.

        Args:
            entry_point (importlib.metadata.EntryPoint):
                The entry point.

        Returns:
            object:
            The processed entry point value.
        """
        return cast(RegistryItemType, entry_point.load())


class OrderedRegistry(Registry[RegistryItemType]):
    """A registry that keeps track of registration order."""

    ######################
    # Instance variables #
    ######################

    #: All registered items by ordering item ID.
    _by_id: dict[int, RegistryItemType]

    #: Ordering item IDs, in order.
    _key_order: list[int]

    def __init__(self) -> None:
        """Initialize the registry."""
        super().__init__()

        self._by_id = {}
        self._key_order = []

    def on_item_registered(
        self,
        item: RegistryItemType,
        /,
    ) -> None:
        """Handle extra steps before registering an item.

        This will place the item in sequential order.

        Subclasses that override this to perform additional post-registration
        operations must first call this method.

        Args:
            item (object):
                The item that was registered.
        """
        item_id = id(item)
        self._key_order.append(item_id)
        self._by_id[item_id] = item

    def on_item_unregistered(
        self,
        item: RegistryItemType,
        /,
    ) -> None:
        """Handle extra steps after unregistering an item.

        Subclasses that override this to perform additional
        post-unregistration operations must first call this method.

        Args:
            item (object):
                The item that was unregistered.
        """
        item_id = id(item)
        del self._by_id[item_id]
        self._key_order.remove(item_id)

    def __iter__(self) -> Iterator[RegistryItemType]:
        """Yield the items in the order they were registered.

        Yields:
            object:
            The registered items.
        """
        self.populate()

        by_id = self._by_id

        for key in self._key_order:
            yield by_id[key]

    def __getitem__(
        self,
        index: int,
    ) -> RegistryItemType:
        """Return an item by its registered index.

        Args:
            index (int):
                The position at which the item was registered. This is 0-based
                and negative indices are supported.

        Returns:
            object:
            The requested item.

        Raises:
            IndexError:
                This exception is raised if the requested index is out of
                range.

            TypeError:
                This exception is raised if the requested index is not an
                integer.
        """
        if not isinstance(index, int):
            raise TypeError('Index is not an integer (is %s).'
                            % type(index).__name__)

        # We don't have to call populate() because calling len() will.
        length = len(self)

        if index < 0:
            index += length

        if index > length:
            raise IndexError('Index is out of range.')

        return self._by_id[self._key_order[index]]
