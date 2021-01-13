# Copyright (c) 2020-2021, LE GOFF Vincent
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


"""Contexts specific to sessions.

Session contexts are called when the character isn't logged in yet,
that is, to handle all the connection process (enter username,
enter password...) and the character creation (and account creation).
Contrary to character contexts (see `character_context.py`),
session contexts can't be stacked: there's one at a time on a session,
no less, no more.

"""

from typing import Union

from context.base import BaseContext, CONTEXTS

class SessionContext(BaseContext):

    """
    Session context, to handle character connections.
    """

    def __init__(self, session):
        self.session = session

    async def msg(self, text: Union[str, bytes]):
        """
        Send some text to the context session.

        Args:
            text (str or bytes): text to send.

        """
        await self.session.msg(text)

    async def move(self, context_path: str):
        """
        Move to a new context.

        You have to specify the new context as a Python path, like
        "connection.motd".  This path is a shortcut to the
        "context.connection.motd" module (unless it has been replaced
        by a plugin).

        Args:
            context_path (str): path to the module where the new context is.

        Note:
            Character contexts cannot be moved with this method.  Use
            the context stack on the character
            (`character.context_stack.add(...)` instead).

        """
        NewContext = CONTEXTS[context_path]
        new_context = NewContext(self.session)
        await self.leave()
        await type(self).condition.mark_as_done(self)
        self.session.context = new_context
        await new_context.enter()
        await self.send_messages()
