"""Unit tests for registries."""

from __future__ import annotations

from typing import Iterable
from unittest import TestCase

from registries.registry import OrderedRegistry


class OrderedRegistryTests(TestCase):
    """Tests for registries.registry.OrderedRegistry."""

    class TestRegistry(OrderedRegistry[int]):
        def get_defaults(self) -> Iterable[int]:
            return [1, 2, 3]

    def test_iteration_order(self) -> None:
        """Testing OrderedRegistry iteration order"""
        registry = self.TestRegistry()

        registry.register(4)
        self.assertListEqual(list(registry),
                             [1, 2, 3, 4])

        registry.unregister(3)
        self.assertListEqual(list(registry),
                             [1, 2, 4])

    def test_getitem(self) -> None:
        """Testing OrderedRegistry.__getitem__"""
        registry = self.TestRegistry()

        self.assertEqual(registry[0], 1)
        self.assertEqual(registry[1], 2)
        self.assertEqual(registry[2], 3)

    def test_getitem_negative_indices(self) -> None:
        """Testing OrderedRegistry.__getitem__ with negative indices"""
        registry = self.TestRegistry()

        self.assertEqual(registry[-1], 3)
        self.assertEqual(registry[-2], 2)
        self.assertEqual(registry[-3], 1)

    def test_getitem_invalid_index(self) -> None:
        """Testing OrderedRegistry.__getitem__ with an invalid index"""
        registry = self.TestRegistry()

        with self.assertRaises(TypeError):
            registry['foo']  # type: ignore

    def test_getitem_out_of_range(self) -> None:
        """Testing OrderedRegistry.__getitem__ with an out of range index"""
        registry = self.TestRegistry()

        with self.assertRaises(IndexError):
            registry[1000]
