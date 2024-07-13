"""Unit tests for registries."""

from __future__ import annotations

import kgb
from typing import Any
from unittest import TestCase

from registries.registry import EntryPointRegistry, entry_points, logger


class _FakeEntryPoint:
    def __init__(
        self,
        *,
        name: str,
        result: Any,
    ) -> None:
        self.name = name
        self.result = result

    def load(self) -> Any:
        return self.result


class EntryPointRegistryTests(kgb.SpyAgency, TestCase):
    """Tests for registries.registry.EntryPointRegistry."""

    def test_get_defaults(self) -> None:
        """Testing EntryPointRegistry.get_defaults"""
        class MyRegistry(EntryPointRegistry):
            entry_point_group = 'entry.points'

        self.spy_on(entry_points, op=kgb.SpyOpReturn([
            _FakeEntryPoint(name='ep1', result=1),
            _FakeEntryPoint(name='ep2', result=2),
            _FakeEntryPoint(name='ep3', result=3),
        ]))

        registry = MyRegistry()

        self.assertEqual(list(registry), [1, 2, 3])

        self.assertSpyCalledWith(entry_points,
                                 group='entry.points')

    def test_get_defaults_with_load_error(self) -> None:
        """Testing EntryPointRegistry.get_defaults"""
        class MyRegistry(EntryPointRegistry):
            entry_point_group = 'entry.points'

            def process_value_from_entry_point(self, entry_point):
                raise Exception('oh no')

        self.spy_on(entry_points, op=kgb.SpyOpReturn([
            _FakeEntryPoint(name='ep1', result=1),
            _FakeEntryPoint(name='ep2', result=2),
            _FakeEntryPoint(name='ep3', result=3),
        ]))

        registry = MyRegistry()

        with self.assertLogs(logger) as cm:
            self.assertEqual(list(registry), [])

        logs = cm.output
        self.assertEqual(len(logs), 3)
        self.assertRegex(
            logs[0],
            '^ERROR:registries.registry:Could not load entry point "ep1" for '
            'registry MyRegistry: oh no.\nTraceback')
        self.assertRegex(
            logs[1],
            '^ERROR:registries.registry:Could not load entry point "ep2" for '
            'registry MyRegistry: oh no.\nTraceback')
        self.assertRegex(
            logs[2],
            '^ERROR:registries.registry:Could not load entry point "ep3" for '
            'registry MyRegistry: oh no.\nTraceback')
