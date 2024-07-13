"""Unit tests for registries."""

from __future__ import annotations

import re
import time
from threading import Lock, Thread
from typing import Any, Callable
from unittest import TestCase

from kgb import SpyAgency

from registries.errors import (AlreadyRegisteredError,
                               AttrNotFoundUnregistrationError,
                               InvalidItemRegistrationError,
                               ItemNotFoundLookupError,
                               ItemNotFoundUnregistrationError,
                               RegistrationConflictError,
                               UnsupportedRegistryAttributeError)
from registries.items import RegistryItemType
from registries.registry import Registry


class Item:
    """An item used for registry tests."""

    ######################
    # Instance variables #
    ######################

    id: int
    name: str
    fake: bool

    def __init__(
        self,
        **attrs,
    ) -> None:
        """Initialize the item.

        Args:
            **attrs (dict):
                Attribute name and value pairs to set on the item.
        """
        self._attrs = set(attr_name for attr_name in attrs)

        for attr_name, attr_value in attrs.items():
            setattr(self, attr_name, attr_value)

    def __repr__(self) -> str:
        attrs = sorted(
            '%s=%r' % (attr_name, getattr(self, attr_name))
            for attr_name in self._attrs
        )
        return '<Item(%s)>' % ', '.join(attrs)

    def __hash__(self) -> int:
        return id(self)

    def __eq__(
        self,
        other: Any,
    ) -> bool:
        return (type(self) is type(other) and
                self._attrs == other._attrs and
                all(getattr(self, attr_name) == getattr(other, attr_name)
                    for attr_name in self._attrs))


class ItemIDRegistry(Registry[Item]):
    lookup_attrs = ('id',)


class ThreadRegistry(Registry[Item]):
    """A registry used for thread tests.

    Version Added:
        5.0
    """

    lookup_attrs = ('id',)

    ######################
    # Instance variables #
    ######################

    count: int
    sleep_lock: Lock

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the registry.

        Args:
            *args (tuple):
                Positional arguments to pass to the parent.

            **kwargs (tuple):
                Keyword arguments to pass to the parent.
        """
        super().__init__(*args, **kwargs)

        self.count = 0
        self.sleep_lock = Lock()

    def sleep_first_thread(self) -> None:
        """Sleep the first time a thread calls this method."""
        with self.sleep_lock:
            do_sleep = (self.count == 0)
            self.count += 1

        if do_sleep:
            time.sleep(0.1)


class RegistryTests(SpyAgency, TestCase):
    """Tests for djblets.registries.Registry."""

    def test_empty_by_default(self) -> None:
        """Testing Registry instances are created empty"""
        registry = Registry()

        self.assertEqual(len(registry), 0)
        self.assertEqual(set(registry), set())

    def test_get_with_pos_arg(self) -> None:
        """Testing Registry.get() with 1 positional argument"""
        registry = ItemIDRegistry()
        item = Item(id=1)

        registry.register(item)

        self.assertIs(registry.get(1), item)

    def test_get_with_pos_arg_multiple_lookup_attrs(self) -> None:
        """Testing Registry.get() with 1 positional argument and multiple
        lookup_attrs
        """
        class MyRegistry(Registry[Item]):
            lookup_attrs = ('id', 'name')

        registry = MyRegistry()
        item = Item(id=1,
                    name='item1')

        registry.register(item)

        message = re.escape(
            'Positional arguments cannot be provided to MyRegistry.get(). '
            'This registry only supports looking up items using keyword '
            'arguments.'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.get(1)

    def test_get_with_multiple_pos_args(self) -> None:
        """Testing Registry.get() with multiple positional arguments"""
        registry = ItemIDRegistry()
        item = Item(id=1)

        registry.register(item)

        message = re.escape(
            'Either one positional argument or one keyword argument may be '
            'provided to ItemIDRegistry.get().'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.get(1, 2)

    def test_get_with_keyword_arg(self) -> None:
        """Testing Registry.get() with one keyword argument"""
        class MyRegistry(Registry):
            lookup_attrs = ('id', 'name')

        registry = MyRegistry()
        item = Item(id=1,
                    name='item1')

        registry.register(item)

        self.assertIs(registry.get(name='item1'), item)
        self.assertIs(registry.get(id=1), item)

    def test_get_with_multiple_keyword_args(self) -> None:
        """Testing Registry.get() with multiple keyword arguments"""
        class MyRegistry(Registry):
            lookup_attrs = ('id', 'name')

        registry = MyRegistry()
        item = Item(id=1,
                    name='item1')

        registry.register(item)

        message = re.escape(
            'Either one positional argument or one keyword argument may be '
            'provided to MyRegistry.get().'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.get(id=1,
                         name='item1')

    def test_get_with_no_args(self) -> None:
        """Testing Registry.get() with no arguments"""
        registry = ItemIDRegistry()
        item = Item(id=1,
                    name='item1')

        registry.register(item)

        message = re.escape(
            'Either one positional argument or one keyword argument may be '
            'provided to ItemIDRegistry.get().'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.get()

    def test_get_with_not_found(self) -> None:
        """Testing Registry.get() with item not found"""
        registry = ItemIDRegistry()
        item = Item(id=1)

        registry.register(item)

        message = re.escape('No item registered with id=123.')

        with self.assertRaisesRegex(ItemNotFoundLookupError, message):
            registry.get(123)

    def test_get_with_invalid_attribute(self) -> None:
        """Testing Registry.get_item with invalid attributes"""
        registry = ItemIDRegistry()

        message = re.escape(
            '"foo" is not a registered lookup attribute.'
        )

        with self.assertRaisesRegex(UnsupportedRegistryAttributeError,
                                    message):
            registry.get(foo='bar')

    def test_get_or_none_with_pos_arg(self) -> None:
        """Testing Registry.get_or_none() with 1 positional argument"""
        registry = ItemIDRegistry()
        item = Item(id=1)

        registry.register(item)

        self.assertIs(registry.get_or_none(1), item)

    def test_get_or_none_with_pos_arg_multiple_lookup_attrs(self) -> None:
        """Testing Registry.get_or_none() with 1 positional argument and
        multiple lookup_attrs
        """
        class MyRegistry(Registry):
            lookup_attrs = ('id', 'name')

        registry = MyRegistry()
        item = Item(id=1,
                    name='item1')

        registry.register(item)

        message = re.escape(
            'Positional arguments cannot be provided to '
            'MyRegistry.get_or_none(). This registry only supports looking '
            'up items using keyword arguments.'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.get_or_none(1)

    def test_get_or_none_with_multiple_pos_args(self) -> None:
        """Testing Registry.get_or_none() with multiple positional arguments"""
        registry = ItemIDRegistry()
        item = Item(id=1)

        registry.register(item)

        message = re.escape(
            'Either one positional argument or one keyword argument may be '
            'provided to ItemIDRegistry.get_or_none().'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.get_or_none(1, 2)

    def test_get_or_none_with_keyword_arg(self) -> None:
        """Testing Registry.get_or_none() with one keyword argument"""
        class MyRegistry(Registry):
            lookup_attrs = ('id', 'name')

        registry = MyRegistry()
        item = Item(id=1,
                    name='item1')

        registry.register(item)

        self.assertIs(registry.get_or_none(name='item1'), item)
        self.assertIs(registry.get_or_none(id=1), item)

    def test_get_or_none_with_multiple_keyword_args(self) -> None:
        """Testing Registry.get_or_none() with multiple keyword arguments"""
        class MyRegistry(Registry):
            lookup_attrs = ('id', 'name')

        registry = MyRegistry()
        item = Item(id=1,
                    name='item1')

        registry.register(item)

        message = re.escape(
            'Either one positional argument or one keyword argument may be '
            'provided to MyRegistry.get_or_none().'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.get_or_none(id=1,
                                 name='item1')

    def test_get_or_none_with_no_args(self) -> None:
        """Testing Registry.get_or_none() with no arguments"""
        class MyRegistry(Registry):
            lookup_attrs = ('id', 'name')

        registry = MyRegistry()
        item = Item(id=1,
                    name='item1')

        registry.register(item)

        message = re.escape(
            'Either one positional argument or one keyword argument may be '
            'provided to MyRegistry.get_or_none().'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.get_or_none()

    def test_get_or_none_with_not_found(self) -> None:
        """Testing Registry.get_or_none() with item not found"""
        registry = ItemIDRegistry()
        item = Item(id=1)

        registry.register(item)

        self.assertIsNone(registry.get_or_none(123))

    def test_get_or_none_with_invalid_attribute(self) -> None:
        """Testing Registry.get_or_none_item with invalid attributes"""
        registry = ItemIDRegistry()

        message = re.escape(
            '"foo" is not a registered lookup attribute.'
        )

        with self.assertRaisesRegex(UnsupportedRegistryAttributeError,
                                    message):
            registry.get_or_none(foo='bar')

    def test_register(self) -> None:
        """Testing Registry.register"""
        registry = ItemIDRegistry()

        self.spy_on(registry.on_item_registering)
        self.spy_on(registry.on_item_registered)

        items = [
            Item(id=1),
            Item(id=2),
            Item(id=3),
        ]

        for item in items:
            registry.register(item)

        self.assertEqual(set(registry), set(items))

        self.assertSpyCallCount(registry.on_item_registering, 3)
        self.assertSpyCalledWith(registry.on_item_registering, items[0])
        self.assertSpyCalledWith(registry.on_item_registering, items[1])
        self.assertSpyCalledWith(registry.on_item_registering, items[2])

        self.assertSpyCallCount(registry.on_item_registered, 3)
        self.assertSpyCalledWith(registry.on_item_registered, items[0])
        self.assertSpyCalledWith(registry.on_item_registered, items[1])
        self.assertSpyCalledWith(registry.on_item_registered, items[2])

    def test_register_with_thread_conflict(self) -> None:
        """Testing Registry.register with same item in different threads
        """
        def _thread_main(
            secs: float,
            item: Item,
            expect_fail: bool,
        ) -> None:
            time.sleep(secs)

            if expect_fail:
                with self.assertRaises(RegistrationConflictError):
                    registry.register(item)
            else:
                registry.register(item)

        class TestRegistry(ThreadRegistry):
            def on_item_registering(
                self,
                item: Item,
            ) -> None:
                self.sleep_first_thread()

        registry = TestRegistry()
        registry.populate()
        self.spy_on(registry.on_item_registering)
        self.spy_on(registry.on_item_registered)

        self.assertEqual(len(registry), 0)

        item1 = Item(id=0)
        item2 = Item(id=0)

        self._run_threads(
            target=_thread_main,
            threads_args=[
                [0.1, item1, True],
                [0.05, item2, False],
            ])

        self.assertIs(registry.get(0), item2)

        self.assertSpyCallCount(registry.on_item_registering, 2)
        self.assertSpyCallCount(registry.on_item_registered, 1)

    def test_unregister(self) -> None:
        """Testing Registry.unregister"""
        registry = ItemIDRegistry()
        items = [
            Item(id=1),
            Item(id=2),
            Item(id=3),
        ]

        self.spy_on(registry.on_item_unregistering)
        self.spy_on(registry.on_item_unregistered)

        for item in items:
            registry.register(item)

        for item in items:
            registry.unregister(item)

        self.assertEqual(set(registry), set())

        self.assertSpyCallCount(registry.on_item_unregistering, 3)
        self.assertSpyCalledWith(registry.on_item_unregistering, items[0])
        self.assertSpyCalledWith(registry.on_item_unregistering, items[1])
        self.assertSpyCalledWith(registry.on_item_unregistering, items[2])

        self.assertSpyCallCount(registry.on_item_unregistered, 3)
        self.assertSpyCalledWith(registry.on_item_unregistered, items[0])
        self.assertSpyCalledWith(registry.on_item_unregistered, items[1])
        self.assertSpyCalledWith(registry.on_item_unregistered, items[2])

    def test_unregister_with_thread_conflict(self) -> None:
        """Testing Registry.unregister with same item in different
        threads
        """
        def _thread_main(
            secs: float,
            expect_fail: bool,
        ) -> None:
            time.sleep(secs)

            if expect_fail:
                with self.assertRaises(ItemNotFoundUnregistrationError):
                    registry.unregister(item1)
            else:
                registry.unregister(item1)

        class TestRegistry(ThreadRegistry):
            def on_item_unregistering(
                self,
                item: Item,
            ) -> None:
                self.sleep_first_thread()

        registry = TestRegistry()
        self.spy_on(registry.on_item_unregistering)
        self.spy_on(registry.on_item_unregistered)

        item1 = Item(id=0)
        registry.register(item1)

        self.assertEqual(len(registry), 1)

        self._run_threads(
            target=_thread_main,
            threads_args=[
                [0.1, True],
                [0.05, False],
            ])

        self.assertEqual(len(registry), 0)
        self.assertSpyCallCount(registry.on_item_unregistering, 2)
        self.assertSpyCallCount(registry.on_item_unregistered, 1)

    def test_unregister_removes_attr_lookups(self) -> None:
        """Testing Registry.unregister removes lookup entries"""
        registry = ItemIDRegistry()
        items = [
            Item(id=0),
            Item(id=1),
            Item(id=2),
        ]

        for item in items:
            registry.register(item)

        for item in items:
            registry.unregister(item)

            message = re.escape(f'No item registered with id={item.id}.')

            with self.assertRaisesRegex(ItemNotFoundLookupError, message):
                registry.get(item.id)

        self.assertEqual(len(registry), 0)

    def test_unregister_by_attr_with_pos_arg(self) -> None:
        """Testing Registry.unregister_by_attr with 1 positional argument"""
        registry = ItemIDRegistry()
        items = [
            Item(id=1),
            Item(id=2),
            Item(id=3),
        ]

        self.spy_on(registry.on_item_unregistering)
        self.spy_on(registry.on_item_unregistered)

        for item in items:
            registry.register(item)

        for item in items:
            registry.unregister_by_attr(item.id)

        self.assertEqual(set(registry), set())

        self.assertSpyCallCount(registry.on_item_unregistering, 3)
        self.assertSpyCalledWith(registry.on_item_unregistering, items[0])
        self.assertSpyCalledWith(registry.on_item_unregistering, items[1])
        self.assertSpyCalledWith(registry.on_item_unregistering, items[2])

        self.assertSpyCallCount(registry.on_item_unregistered, 3)
        self.assertSpyCalledWith(registry.on_item_unregistered, items[0])
        self.assertSpyCalledWith(registry.on_item_unregistered, items[1])
        self.assertSpyCalledWith(registry.on_item_unregistered, items[2])

    def test_unregister_by_attr_with_pos_arg_multiple_lookup_args(
        self,
    ) -> None:
        """Testing Registry.unregister_by_attr with 1 positional argument and
        multiple lookup_attrs
        """
        class MyRegistry(Registry[Item]):
            lookup_attrs = ('id', 'name')

        registry = MyRegistry()

        message = re.escape(
            'Positional arguments cannot be provided to '
            'MyRegistry.unregister_by_attr(). This registry only supports '
            'looking up items using keyword arguments.'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.unregister_by_attr(1)

    def test_unregister_by_attr_with_multiple_pos_args(
        self,
    ) -> None:
        """Testing Registry.unregister_by_attr with mulitple positional
        arguments
        """
        registry = ItemIDRegistry()

        message = re.escape(
            'Either one positional argument or one keyword argument may be '
            'provided to ItemIDRegistry.unregister_by_attr().'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.unregister_by_attr(1, 2)

    def test_unregister_by_attr_with_keyword_arg(self) -> None:
        """Testing Registry.unregister_by_attr with 1 keyword argument"""
        registry = ItemIDRegistry()
        items = [
            Item(id=1),
            Item(id=2),
            Item(id=3),
        ]

        self.spy_on(registry.on_item_unregistering)
        self.spy_on(registry.on_item_unregistered)

        for item in items:
            registry.register(item)

        for item in items:
            registry.unregister_by_attr(id=item.id)

        self.assertEqual(set(registry), set())

        self.assertSpyCallCount(registry.on_item_unregistering, 3)
        self.assertSpyCalledWith(registry.on_item_unregistering, items[0])
        self.assertSpyCalledWith(registry.on_item_unregistering, items[1])
        self.assertSpyCalledWith(registry.on_item_unregistering, items[2])

        self.assertSpyCallCount(registry.on_item_unregistered, 3)
        self.assertSpyCalledWith(registry.on_item_unregistered, items[0])
        self.assertSpyCalledWith(registry.on_item_unregistered, items[1])
        self.assertSpyCalledWith(registry.on_item_unregistered, items[2])

    def test_unregister_by_attr_with_multiple_keyword_args(
        self,
    ) -> None:
        """Testing Registry.unregister_by_attr with mulitple keyword
        arguments
        """
        registry = ItemIDRegistry()

        message = re.escape(
            'Either one positional argument or one keyword argument may be '
            'provided to ItemIDRegistry.unregister_by_attr().'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.unregister_by_attr(id=1,
                                        name='item1')

    def test_unregister_by_attr_with_no_args(self) -> None:
        """Testing Registry.unregister_by_attr with no arguments"""
        registry = ItemIDRegistry()

        message = re.escape(
            'Either one positional argument or one keyword argument may be '
            'provided to ItemIDRegistry.unregister_by_attr().'
        )

        with self.assertRaisesRegex(TypeError, message):
            registry.unregister_by_attr()

    def test_unregister_by_attr_with_not_found(self) -> None:
        """Testing Registry.unregister_by_attr with not found"""
        registry = ItemIDRegistry()

        message = re.escape('No item registered with id=123.')

        with self.assertRaisesRegex(AttrNotFoundUnregistrationError, message):
            registry.unregister_by_attr(id=123)

    def test_unregister_by_attr_with_invalid_attribute(self) -> None:
        """Testing Registry.unregister_by_attr with invalid attributes"""
        registry = ItemIDRegistry()

        message = re.escape(
            '"foo" is not a registered lookup attribute.'
        )

        with self.assertRaisesRegex(UnsupportedRegistryAttributeError,
                                    message):
            registry.unregister_by_attr(foo='bar')

    def test_populate(self) -> None:
        """Testing Registry.populate"""
        item1 = Item(id=0)
        item2 = Item(id=1)

        class TestRegistry(ItemIDRegistry):
            def get_defaults(self):
                yield item1
                yield item2

        registry = TestRegistry()
        self.spy_on(registry.on_populated)
        self.spy_on(registry.on_populating)

        registry.populate()

        self.assertEqual(registry._registry, {
            'id': {
                0: item1,
                1: item2,
            },
        })

        self.assertSpyCalled(registry.on_populated)
        self.assertSpyCalled(registry.on_populating)

        self.assertIs(registry.get(item1.id), item1)
        self.assertIs(registry.get(item2.id), item2)

    def test_populate_with_thread_conflict(self) -> None:
        """Testing Registry.populate with multiple threads"""
        def _thread_main(
            secs: float,
        ) -> None:
            time.sleep(secs)
            registry.populate()

            self.assertEqual(list(registry._items), [item1, item2])

        class TestRegistry(ThreadRegistry):
            def get_defaults(self):
                yield item1
                yield item2

            def on_populating(self) -> None:
                self.sleep_first_thread()

        registry = TestRegistry()
        self.spy_on(registry.on_populating)
        self.spy_on(registry.on_populated)

        item1 = Item(id=0)
        item2 = Item(id=1)

        self._run_threads(
            target=_thread_main,
            threads_args=[
                [0.1],
                [0.05],
            ])

        self.assertEqual(list(registry._items), [item1, item2])
        self.assertSpyCallCount(registry.on_populating, 1)
        self.assertSpyCallCount(registry.on_populated, 1)

    def test_population_on_register(self) -> None:
        """Testing Registry.register_item triggers population before
        registration
        """
        original_item = Item(id=0)
        duplicate_item = Item(id=0, fake=True)

        class TestRegistry(ItemIDRegistry):
            def get_defaults(self):
                yield original_item

        registry = TestRegistry()

        message = re.escape(
            'Could not register <Item(fake=True, id=0)>: another item '
            '(<Item(id=0)>) is already registered with id=0.'
        )

        with self.assertRaisesRegex(RegistrationConflictError, message):
            registry.register(duplicate_item)

        self.assertIs(registry.get(original_item.id),
                      original_item)

    def test_population_on_unregister(self) -> None:
        """Testing Registry.unregister triggers population before
        unregistration.
        """
        item = Item(id=0)

        class TestRegistry(ItemIDRegistry):
            def get_defaults(self):
                yield item

        registry = TestRegistry()
        registry.unregister(item)
        self.assertEqual(len(registry), 0)

    def test_registering_duplicate(self) -> None:
        """Testing Registry.register_item with duplicate items"""
        registry = ItemIDRegistry()

        item = Item(id=1)
        registry.register(item)

        message = re.escape(
            'Could not register <Item(id=1)>: it is already registered.'
        )

        with self.assertRaisesRegex(AlreadyRegisteredError, message):
            registry.register(item)

    def test_registering_duplicate_attributes(self) -> None:
        """Testing Registry.register_item with items that have identical
        attributes
        """
        registry = ItemIDRegistry()
        registry.register(Item(id=0, name='foo'))

        message = re.escape(
            "Could not register <Item(id=0, name='bar')>: another item "
            "(<Item(id=0, name='foo')>) is already registered with id=0."
        )

        with self.assertRaisesRegex(RegistrationConflictError, message):
            registry.register(Item(id=0,
                                   name='bar'))

    def test_register_missing_attributes(self) -> None:
        """Testing Registry.register_item with items that have missing
        attributes
        """
        registry = ItemIDRegistry()

        message = re.escape(
            'Could not register <Item()>: it does not have a "id" attribute.'
        )

        with self.assertRaisesRegex(InvalidItemRegistrationError, message):
            registry.register(Item())

    def test_reset(self) -> None:
        """Testing Registry.reset"""
        item1 = Item(id=0)
        item2 = Item(id=1)

        class TestRegistry(ItemIDRegistry):
            def get_defaults(self):
                yield item1
                yield item2

        registry = TestRegistry()
        self.spy_on(registry.on_resetting)
        self.spy_on(registry.on_reset)

        registry.populate()
        registry.reset()

        self.assertEqual(registry._registry, {
            'id': {},
        })

        self.assertSpyCalled(registry.on_resetting)
        self.assertSpyCalled(registry.on_reset)

    def test_reset_with_thread_conflict(self) -> None:
        """Testing Registry.reset with multiple threads"""
        def _thread_main(
            secs: float,
        ) -> None:
            self.assertEqual(list(registry._items), [item1, item2])

            time.sleep(secs)
            registry.reset()

            self.assertEqual(list(registry._items), [])

        class TestRegistry(ThreadRegistry):
            def get_defaults(self):
                yield item1
                yield item2

            def on_resetting(self) -> None:
                self.sleep_first_thread()

        item1 = Item(id=0)
        item2 = Item(id=1)

        registry = TestRegistry()
        registry.populate()
        self.spy_on(registry.on_resetting)
        self.spy_on(registry.on_reset)

        self._run_threads(
            target=_thread_main,
            threads_args=[
                [0.1],
                [0.05],
            ])

        self.assertEqual(len(registry._items), 0)
        self.assertSpyCallCount(registry.on_resetting, 1)
        self.assertSpyCallCount(registry.on_reset, 1)

    def test_contains(self) -> None:
        """Testing Registry.__contains__"""
        registry = ItemIDRegistry()

        item1 = Item(id=1)
        item2 = Item(id=2)
        registry.register(item1)

        self.assertIn(item1, registry)
        self.assertNotIn(item2, registry)

    def test_error_override(self) -> None:
        """Testing Registry error formatting strings"""
        class MyError(ItemNotFoundUnregistrationError[RegistryItemType]):
            message_template = 'The foo "%(item)s" is unregistered.'

        class TestRegistry(Registry[int]):
            item_not_found_unregistration_error_cls = MyError

        registry = TestRegistry()

        message = re.escape('The foo "1" is unregistered.')

        with self.assertRaisesRegex(ItemNotFoundUnregistrationError, message):
            registry.unregister(1)

    def _run_threads(
        self,
        target: Callable[..., None],
        threads_args: list[list[Any]],
    ) -> None:
        """Run tests with a specified number of threads.

        This will create multiple threads with the same target and different
        arguments, starting them up and then joining them back to the main
        thread.

        Args:
            target (callable):
                The function for each thread to call when started.

            threads_args (list):
                Arguments to provide for each created thread.

                The number of items in this list dictates the number of
                threads.
        """
        threads = [
            Thread(target=target,
                   args=thread_args)
            for thread_args in threads_args
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
