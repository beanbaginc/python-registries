=====================
Registries for Python
=====================

Registries is a module for managing collections of objects, allowing for easy
registration, lookups, and access.

This is ideal for applications that need to manage abstract interfaces with
backend implementations, such as plugins, extensions, and other cases where
you'd employ a Registry Pattern.


What is the Registry Pattern?
=============================

The Registry Pattern is a design pattern that provides a central repository
for storing and accessing instances of various classes or objects. Objects can
be registered dynamically or as part of the registry definition, each with a
unique identifier, and then retrieved later by iterating through or querying
the registry.

This can help provide a more decoupled design, reducing the need for
dependencies between parts of your codebase, and helping make your codebase
more extensible, maintainable, and testable.

Registries for Python makes this simple.


Features
========

Registries offers:

* **Dynamic registration** and unregistration of items.
* **Flexible lookups** based on registered lookup attributes.
* **Thread-safety** to avoid conflicts with modifying a registry.
* **Extensibility** through pre/post hooks for registration, unregistration,
  initial population, and resetting of registries.
* **Python type hints** to ease development.
* **Built-in registries** for order-dependent items and wrapping around
  `Python Entry Points`_.


.. _Python Entry Points:
   https://packaging.python.org/en/latest/specifications/entry-points/


Installation
============

To install Registries, run:

.. code-block:: console

   $ pip install registries

Registries follows `semantic versioning`_, meaning no surprises when you
upgrade.

.. _semantic versioning: https://semver.org/


Example Usage
-------------

Here's a quick example to get you started with Registries:

.. code-block:: python

   from typing import Type

   from registries import Registry


   # Let's create a base class for our objects and some default items.
   class BaseItem:
       my_item_id: str


   class FooItem(BaseItem):
       my_item_id = 'fooitem'


   class BarItem(BaseItem):
       my_item_id = 'baritem'


   # Now we'll create our registry with those items as defaults.
   class MyRegistry(Registry[Type[BaseItem]]):
       lookup_attrs = ('my_item_id',)

       def get_defaults(self):
           return [FooItem, BarItem]


   # Set up our registry.
   registry = MyRegistry()

   # This will print FooItem and BarItem.
   for item in registry:
       print(item)


   # Let's register a new item.
   class BazItem(BaseItem):
       my_item_id = 'bazitem'


   registry.register(BazItem)


   # BazItem will now be in the registry.
   assert BazItem in registry

   for item in registry:
       print(item)


   # Let's look up some objects.
   assert registry.get('fooitem') is FooItem
   assert registry.get('bazitem') is BazItem


   # We can also look up by explicit attributes, in case the registry supports
   # multiple lookup attributes.
   assert registry.get(my_item_id='baritem') is BarItem


   # Let's unregister FooItem.
   registry.unregister(FooItem)

   assert FooItem not in registry


Documentation
=============

.. toctree::
   :maxdepth: 3

   guides/index
   coderef/index
   releasenotes/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
