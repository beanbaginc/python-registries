==================
Writing Registries
==================

To write a registry, you'll first need to subclass one of the following
registry classes:

* :py:class:`registries.registry.Registry`: The standard Registry class.
* :py:class:`registries.registry.OrderedRegistry`: A registry that maintains
  registration order.
* :py:class:`registries.registry.EntryPointRegistry`: A registry populated by
  `Python Entry Points`_.

We'll cover each of these.


Standard Registries
===================

To create a registry:

1. Subclass :py:class:`~registries.registry.Registry` and pass an item type.
2. Set the :py:attr:`lookup_attrs <registries.registry.Registry.lookup_attrs>`
   attribute.
3. Optionally, provide defaults for the registry.

For example, to create a registry that stored subclasses of a base class:

.. code-block:: python

   from registries import Registry


   class BaseItemType:
       my_id: str


   class DefaultItem1(BaseItemType):
       my_id = 'item1'


   class DefaultItem2(BaseItemType):
       my_id = 'item2'


   class MyRegistry(Registry[Type[MyItemType]]):
       lookup_attrs = ('my_id',)

       def get_defaults(self):
           return [
               DefaultItem1,
               DefaultItem2,
           ]


Or, to create a registry that stores instances of a class:

.. code-block:: python

   from dataclasses import dataclass

   from registries import Registry


   @dataclass
   class ItemType:
       my_id: str


   class MyRegistry(Registry[ItemType]):
       lookup_attrs = ('my_id',)

       def get_defaults(self):
           return [
               ItemType(my_id='item1'),
               ItemType(my_id='item2'),
           ]


You're now set to register and look up items!


Ordered Registries
==================

Ordered registries work just like standard registries, but they track
registration order of items. This ensures that when you iterate through a
registry, the results will be in the same order in which they were registered.

To create an ordered registry, simply subclass
:py:class:`~registries.registry.OrderedRegistry` instead:

.. code-block:: python

   from registries import OrderedRegistry


   class MyRegistry(OrderedRegistry[ItemType]):
       ...


Entry Point Registries
======================

An Entry Point Registry will scan the specified `Python Entry Points`_
group and turn any results into defaults for the registry. This is a great
way of combining the best aspects of registries with Python Entry Points.

To define an Entry Point Registry:

1. Subclass :py:class:`~registries.registry.EntryPointRegistry`.
2. Set the :py:attr:`lookup_attrs <registries.registry.Registry.lookup_attrs>`
   attribute.
3. Set the :py:attr:`entry_point_group
   <registries.registry.EntryPointRegistry.entry_point_group>` attribute.
4. Optionally, override :py:meth:`process_value_from_entry_point()
   <registries.registry.EntryPointRegistry.process_value_from_entry_point>`
   to change what item is returned from a loaded entry point.

For example:

.. code-block:: python

   from registries import EntryPointRegistry


   class BaseItemType:
       name: str


   class MyRegistry(EntryPointRegistry[BaseItemType]):
       lookup_attrs = ('name',)
       entry_point_group = 'myproject.item_modules'

       # Optionally, to return soem attribute of a loaded entry point:
       def process_value_from_entry_point(self, entry_point):
           return entry_point.load().item_instance


Customizing Registry Errors
===========================

Registries make use of a handful of error classes to inform callers when
there are issues registering items, unregistering items, or looking up items.

A custom registry that subclass any of these error classes and set them on
the registry. The following are supported:

* :py:attr:`~registries.registry.Registry.already_registered_error_cls`
  (:py:class:`~registries.errors.AlreadyRegisteredError`)

* :py:attr:`~registries.registry.Registry.
  attr_not_found_unregistration_error_cls`
  (:py:class:`~registries.errors.AttrNotFoundUnregistrationError`)

* :py:attr:`~registries.registry.Registry.invalid_item_registration_error_cls`
  (:py:class:`~registries.errors.InvalidItemRegistrationError`)

* :py:attr:`~registries.registry.Registry.item_not_found_lookup_error_cls`
  (:py:class:`~registries.errors.ItemNotFoundLookupError`)

* :py:attr:`~registries.registry.Registry.
  item_not_found_unregistration_error_cls`
  (:py:class:`~registries.errors.ItemNotFoundUnregistrationError`)

* :py:attr:`~registries.registry.Registry.registration_conflict_error_cls`
  (:py:class:`~registries.errors.RegistrationConflictError`)

* :py:attr:`~registries.registry.Registry.unsupported_registry_attr_error_cls`
  (:py:class:`~registries.errors.UnsupportedRegistryAttributeError`)

Each exception class be customized by overriding the
:py:attr:`~registries.errors.BaseRegistryError.message_template` attribute.

Here's an example of overriding the error used when failing to look up an
item:

.. code-block:: python

   from registries import Registry
   from registries.errors import ItemNotFoundLookupError


   class MyItemNotFoundLookupError(ItemNotFoundLookupError):
       message_template = (
           'A registered MyItemType subclass could not be found with an '
           'attribute of %(attr_name)r and a value of %(attr_value)r.'
       )


   class MyRegistry(Registry[MyItemType]):
       item_not_found_lookup_error_cls = MyItemNotFoundLookupError

       ...


.. _Python Entry Points:
   https://packaging.python.org/en/latest/specifications/entry-points/
