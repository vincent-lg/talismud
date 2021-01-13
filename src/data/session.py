# Copyright (c) 2020-20201, LE GOFF Vincent
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
import pickle
import typing as ty
from uuid import UUID, uuid4

from pony.orm import Optional, PrimaryKey, Required, Set

from context.base import CONTEXTS
from data.base import db, PicklableEntity
from data.decorators import lazy_property
from data.handlers import OptionHandler
import settings

# Asynchronous queue of all session output messages
OUTPUT = {
    "unknown": asyncio.Queue(),
}
CMDS_TO_PORTAL = asyncio.Queue()

class Session(PicklableEntity, db.Entity):

    """
    Session entity.

    A session is an object identifying a live connection.  Each time
    a user connects, a session is created with a different identifier
    (UUID).  Each time this connection is broken, the session is destroyed.
    Connections can store data (through the option handler and the
    attributes handler).

    Note: if a user connects to the portal, a session is created in the
    game database.  Should the connection remain live but the game be
    restarted, the connection is maintained and the session information
    is retrieved from the database.

    Web sessions, created by the webserver to keep persistent data,
    are stored in the WebSession entity (see web.session.WebSession).

    """

    uuid = PrimaryKey(UUID, default=uuid4)
    context_path = Required(str)
    account = Optional("Account")
    character = Optional("Character")
    binary_options = Required(bytes, default=pickle.dumps({}))

    @lazy_property
    def context(self):
        """Find the context."""
        Context = CONTEXTS[self.context_path]
        return Context(self)

    @context.setter
    def context(self, context):
        """Change the session's context."""
        self.context_path = context.pyname

    @property
    def focused_context(self):
        """Return the focused context."""
        # If there's a character, return the character's active context.
        if (character := self.character):
            return character.context_stack.active_context

        # Otherwise, return the session context
        return self.context

    @lazy_property
    def options(self):
        """Return the session option handler."""
        return OptionHandler(self)

    async def msg(self, text: ty.Union[str, bytes]):
        """
        Send some text to the session.

        Args:
            text (str or bytes): the text to send, encoded or not.

        Sending bytes allows to bypass session encoding, which might
        be handy for encoding test on the client side, for instance.

        Awaiting on this method does not guarantee the message is
        sent to the client.  The relationship between game session
        and portal session is not strongly maintained to avoid
        slowing the game down if the portal is busy.  Therefore,
        if you await on a `session.msg`, be aware that the text
        might not be sent to the client when the method returns.

        Note about encoding:
            If the sent text should be encoded (that is, if its type
            is `str`), the session encoding is first selected, if it
            exists.  The session encoding is stored in the session
            options `session.options["encoding"]`.  The
            `settings.DEFAULT_ENCODING` is used if the session
            didn't specify any encoding.  By default, errors
            during the process are replaced, so accented letters not
            supported by the specified encoding will appear as ?.

        """
        if isinstance(text, str):
            encoding = self.options.get("encoding", settings.DEFAULT_ENCODING)
            try:
                encoded = text.encode(encoding, errors="replace")
            except LookupError:
                # Use utf-8 as a default
                encoding = "utf-8"
                encoded = text.encode(encoding, errors="replace")
        else:
            encoded = text

        try:
            queue = OUTPUT[self.uuid]
        except KeyError:
            queue = OUTPUT["unknown"]

        await queue.put(encoded)

    async def msg_portal(self, cmd_name: str, args: ty.Optional[dict] = None):
        """
        Send a command to the portal.

        This highly-specialized method sends a command to the portal
        process, through the CRUX server.  Using this method should
        be reserved for small actions with a limited control, unless
        you want to use the great power of some of these commands,
        like "restart_game".  Be aware that sending a command to the
        portal can do a lot of things, including damage.

        Args:
            cmd_name (str): the command name to send.
            args (dict, optional): the arguments of this command.

        """
        args = args or {}
        await CMDS_TO_PORTAL.put((cmd_name, args))
