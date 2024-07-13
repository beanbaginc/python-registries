=================
Item Registration
=================

Registering Items
=================

Registration is simple. You only need to call :py:meth:`Registry.register()
<registries.registry.Registry.register>`.

Make sure you've provided an object or class with a unique value for the
registry's lookup attributes.

For example:

.. code-block:: python

   from myproject.registry import BaseItem, my_registry


   class MyNewItem(BaseItem):
       my_id = 'new-item'


   my_registry.register(MyNewItem)


When registering, the following exceptions can be raised:

* :py:class:`~registries.errors.BaseRegistrationError`:
  Base class for any registration errors.

* :py:class:`~registries.errors.AlreadyRegisteredError`:
  The item has already been registered.

* :py:class:`~registries.errors.RegistrationConflictError`:
  Another item with the same lookup attributes has already been registered.

* :py:class:`~registries.errors.InvalidItemRegistrationError`:
  The item is missing the required lookup attributes.


Unregistering Items
===================

Items can be unregistered using one of two methods:

* :py:meth:`~registries.registry.Registry.unregister`:
  Unregister the exact item that was previously registered.

* :py:meth:`~registries.registry.Registry.unregister_by_attr`:
  Unregister an item based on the lookup attributes.

For example:

.. code-block:: python

   from myproject.registry import BaseItem, my_registry


   class MyNewItem(BaseItem):
       my_id = 'new-item'

   ...

   # Unregister the formerly-registered item.
   my_registry.unregister(MyNewItem)

   # Or unregister by attribute value (if the registry only uses a single
   # lookup attribute).
   my_registry.unregister_by_attr('new-item')

   # Or unregister by specific lookup attributes:
   my_registry.unregister_by_attr(my_id='new-item')

When unregistering, the following exceptions can be raised:

* :py:class:`~registries.errors.BaseUnregistrationError`:
  Base class for any unregistration errors.

* :py:class:`~registries.errors.AttrNotFoundUnregistrationError`:
  The item could not be found when unregistering by attribute.

* :py:class:`~registries.errors.ItemNotFoundUnregistrationError`:
  The item could not be found when unregistering by item.
