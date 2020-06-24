# Copyright (c) 2020, LE GOFF Vincent
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""Properties for the database models."""

_MISSING = object()

class LazyPropertyDescriptor:

    """
    Delays loading of property until first access.

    Although extended, this was inspired by Evennia's utility
    (wwww.evennia.com), itself based on the iplementation in the
    werkzeug suite:
        http://werkzeug.pocoo.org/docs/utils/#werkzeug.utils.cached_property

    A lazy property should be used as a decorator over the getter method,
    just like a property.  The difference is that a lazy property will
    call the getter method only once, the first time for this object, and
    then cache the result for following queries.  This allows for fast-access
    to handlers that are not re-created each time the property is called:

        ```python
        class SomeTest(db.Entity):
            @lazy_property
            def db(self):
                return AttributeHandler(self)

            @db.setter
            def db(self, handler):
                raise ValueError("you can't change that")
        ```

    Once initialized, the `AttributeHandler` will be available as a
    property "db" on the object.

    """

    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset
        self.memory = {}

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        # The value might be cached in `memory`
        identifier = hash(instance)
        value = self.memory.get(identifier, _MISSING)
        if value is _MISSING:
            value = self.fget(instance)
            self.memory[identifier] = value

        return value

    def __set__(self, instance, value):
        if not self.fset:
            raise AttributeError("can't set attribute")

        identifier = hash(instance)
        self.fset(instance, value)
        self.memory[identifier] = value

    def setter(self, func):
        self.fset = func
        return self

def lazy_property(func):
    return LazyPropertyDescriptor(func)
