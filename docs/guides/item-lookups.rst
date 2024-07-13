============
Item Lookups
============

Looking Up Items
================

To look up an item, use one of the following methods:

* :py:meth:`~registries.registry.Registry.get`: Look up an item, raising an
  exception if it could not be found.

* :py:meth:`~registries.registry.Registry.get_or_none`: Look up an item,
  returning ``None`` if it could not be found.

.. code-block:: python

   class MyNewItem(BaseItem):
       my_id = 'new-item'

   my_registry.register(MyNewItem)

   # Look up by attribute value (if the registry only uses a single
   # lookup attribute).
   item = my_registry.get('new-item')

   # Look up by a specific lookup attribute:
   item = my_registry.get(my_id='new-item')

   # Look up and return None if the attribute could not be found.
   item = my_registry.get_or_none('new-item')

When looking up, the following exceptions can be raised:

* :py:class:`~registries.registry.Registry.BaseRegistryItemLookupError`:
  Base class for any lookup errors.

* :py:class:`~registries.registry.Registry.ItemNotFoundLookupError`:
  The item could not be found.


Check Item Registration
=======================

To check if an item is in the registry:

.. code-block:: python

   if item in my_registry:
       ...


Iterating Through Items
=======================

You can iterate through all items in the registry:

.. code-block:: python

   for item in my_registry:
       ...
