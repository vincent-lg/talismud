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

"""Cache mixin.

A cache is somewhat similar to a storage, but it doesn't store anything
except in memory.  This is just a convenience to store non-persistent
data that can still be retrieved, should the game restart, but that
are stored in the cache for greater ease otherwise.

"""

from collections.abc import MutableMapping

from data.properties import lazy_property

class HasCache:

    """
    Mixin to add the cache to entities.

    The cache handler is an object that can be manipulated just like
    a dictionary, in a similar way to the storage.  However, nothing
    is stored in the database through the cache, the data isn't
    persisted:

        >>> character.cache["gold"] = 5
        >>> character.cache["gold"]
        5
        >>> del character.cache["gold"]
        >>> character.cache["something"] = 1
        >>> # ... assuming the game restarts here
        ... character.cache.get("something", 0)
        0

    """

    @staticmethod
    def extend_entity(cls):
        """Add entity attributes to the entity."""
        pass

    @lazy_property
    def cache(self):
        """Return the handler for the cache."""
        return CacheHandler(self)


class CacheHandler(MutableMapping):

    """Handler for memorizing data in a dictionary."""

    __slots__ = ("owner", "data")

    def __init__(self, owner):
        self.owner = owner
        self.data = {}

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]
