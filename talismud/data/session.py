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

"""Session entity."""

import asyncio
from collections.abc import MutableMapping
import pickle
from typing import Union
from uuid import UUID, uuid4

from pony.orm import Optional, PrimaryKey, Required, Set

from context.base import BaseContext
from data.attribute import AttributeHandler
from data.base import db, PicklableEntity
from data.properties import lazy_property

# Asynchronous queue of all session output messages
OUTPUT = asyncio.Queue()

class Session(PicklableEntity, db.Entity):

    """
    Session entity.

    A session is an object identifying a live connection.  Each time
    a user connects, a session is created with a different identifier
    (UUID).  Each time this connection is broken, the session is destroyed.
    Connections can store data (through the storage handler and the
    attributes handler).

    Note: if a user connects to the portal, a session is created in the
    game database.  Should the connection remain live but the game be
    restarted, the connection is maintained and the session information
    is retrieved from the database.

    """

    uuid = PrimaryKey(UUID, default=uuid4)
    context_path = Required(str, max_len=64)
    account = Optional("Account")
    attributes = Set("SessionAttribute")
    db_storage = Required(bytes, default=pickle.dumps({}))

    @lazy_property
    def db(self):
        return AttributeHandler(self)

    @lazy_property
    def context(self):
        """Find the context."""
        Context = BaseContext.find_context(self.context_path)
        return Context(self)

    @context.setter
    def context(self, context):
        """Change the session's context."""
        self.context_path = type(context).__module__

    @lazy_property
    def storage(self):
        """Return the handler for the session storage."""
        return StorageHandler(self)

    async def msg(self, text: Union[str, bytes]):
        """
        Send some text to the session.

        Args:
            text (str or bytes): the text to send, encoded or not.

        Sending bytes allows to bypass session encoding, which might
        be handy for encoding test on the client side, for instance.

        """
        if isinstance(text, str):
            encoded = text.encode("ISO-8859-15")
        else:
            encoded = text

        await OUTPUT.put((self.uuid, encoded))


class StorageHandler(MutableMapping):

    """
    Handler for storing data in a dictionary.

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
