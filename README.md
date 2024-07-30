# Registries for Python

[Registries](https://pypi.org/project/registries) is a module for managing
collections of objects, allowing for easy registration, lookups, and access.

This is ideal for applications that need to manage abstract interfaces with
backend implementations, such as plugins, extensions, and other cases where
you'd employ a Registry Pattern.

Registries was built to help develop
[Review Board](https://www.reviewboard.org), our premier code review product
from [Beanbag](https://www.beanbaginc.com), and we're making it available for
use in other projects.


## What is the Registry Pattern?

The Registry Pattern is a design pattern that provides a central repository for
storing and accessing instances of various classes or objects. Objects can be
registered dynamically or as part of the registry definition, each with a
unique identifier, and then retrieved later by iterating through or querying
the registry.

This can help provide a more decoupled design, reducing the need for
dependencies between parts of your codebase, and helping make your codebase
more extensible, maintainable, and testable.

Registries for Python makes this simple.


## Features

Registries offers:

* **Dynamic registration** and unregistration of items.
* **Flexible lookups** based on registered lookup attributes.
* **Thread-safety** to avoid conflicts with modifying a registry.
* **Extensibility** through pre/post hooks for registration, unregistration,
  initial population, and resetting of registries.
* **Python type hints** to ease development.
* **Built-in registries** for order-dependent items and wrapping around
  [Python Entry Points](https://packaging.python.org/en/latest/specifications/entry-points/).


## Installation

To install Registries, run:

```console
$ pip install registries
```

Registries follows [semantic versioning](https://semver.org/), meaning no
surprises when you upgrade.


## Example Usage

Here's a quick example to get you started with Registries:

```python
from typing import Type

from registries import Registry
from registries.errors import RegistrationConflictError


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


# Registering another item with the same ID will raise a
# RegistrationConflictError.
class ConflictItem(BaseItem):
    my_item_id = 'fooitem'

try:
    registry.register(ConflictItem)
except RegistrationConflictError:
    print('ConflictItem conflicts with FooItem!')


# Let's unregister FooItem.
registry.unregister(FooItem)

assert FooItem not in registry

# And now we can register ConflictItem!
registry.register(ConflictItem)
assert registry.get(my_item_id='fooitem') is ConflictItem
```

This is just a quick overview of how you might work with a registry. There's a
lot more that can be done, including:

* Custom registry-defined error messages and exception classes.
* Multi-attribute registration and lookup.
* Hooks for customization the registration and lookup process, to tie into
  other pieces of your architecture.

All thread-safe, all in your control.


## License

Registries is available under the MIT license.


## Contributing

Contributions to Registries can be made on our
[Review Board](https://www.reviewboard.org/) server at
https://reviews.reviewboard.org/.

To post a change for review:

1. Download RBTools:

   ```console
   $ pip install rbtools
   ```

2. Create a branch in your Git clone and make your changes.

3. Post the change for review:

   ```console
   $ rbt post
   ```

   To update your change:

   ```console
   $ rbt post -u
   ```


Our Other Projects
------------------

* [Review Board](https://www.reviewboard.org) -
  Our open source, extensible code review, document review, and image review
  tool.

* [Djblets](https://github.com/djblets/djblets/) -
  Our pack of Django utilities for datagrids, API, extensions, and more. Used
  by Review Board.

* [Housekeeping](https://github.com/beanbaginc/housekeeping) -
  Deprecation management for Python modules, classes, functions, and
  attributes.

* [kgb](https://github.com/beanbaginc/kgb) -
  A powerful function spy implementation to help write Python unit tests.

* [Typelets](https://github.com/beanbaginc/python-typelets) -
  Type hints and utility objects for Python and Django projects.

You can see more on [github.com/beanbaginc](https://github.com/beanbaginc) and
[github.com/reviewboard](https://github.com/reviewboard).
