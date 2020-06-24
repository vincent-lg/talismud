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

"""Storage mixin.

Contrary to attributes, a storage simply is an internatl dictionary-like
object, stored in the database, as an additional field (db_storage)
which contains only a binary (pickled dictionary).

"""

from collections.abc import MutableMapping
import pickle

from pony.orm import Required

from data.base import db
from data.properties import lazy_property

class HasStorage:

    """
    Mixin to add the notion of storage to an entity.

    The storage handler is an object which uses a binary representation,
    stored in the entity itself.  It has all the methods one can expect
    from a dictionary and can be used as such.

        >>> session.storage["username"] = "someone"
        >>> session.storage["username"]
        'someone'
        >>> len(session.storage)
        1
        >>> del session.storage["username"]
        >>> sesession.storage.get("username", "")
        ''
        >>> # ...

    Because this binary is stored in the entity itself, the stored
    information won't create new database rows.  Retrieving them will
    be quicker than using attributes for instance.  However, such
    is not the case should the storage grow to a large collection.
    Therefore, it is still recommended to store "rather small"
    data in the storage, and use attributes otherwise.

    Also keep in mind that database queries won't be able to look for
    a particular information in the storage.  You cannot ask to retrieve
    each session having, say, a stored "username" of "someone".
    That's another strength of attributes.

    """

    @staticmethod
    def extend_entity(cls):
        """Add entity attributes to the entity."""
        cls.db_storage = Required(bytes, default=pickle.dumps({}))

    @lazy_property
    def storage(self):
        """Return the handler for the storage."""
        return StorageHandler(self)


class StorageHandler(MutableMapping):

    """Handler for storing data in a dictionary."""

    __slots__ = ("owner", "data")

    def __init__(self, owner):
        self.owner = owner
        self.data = pickle.loads(owner.db_storage)

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        self.owner.db_storage = pickle.dumps(self.data)

    def __delitem__(self, key):
        del self.data[key]
        self.owner.db_storage = pickle.dumps(self.data)
