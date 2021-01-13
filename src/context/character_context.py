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


"""Contexts specific to characters.

Character contexts are used when a character has logged in.  Contrary
to session contexts (see `session_context.py`), character contexts
can be stacked simultaneously.

"""

from typing import Optional, Union

from context.base import BaseContext

class CharacterContext(BaseContext):

    """
    Character context, to be used when the character is logged in.
    """

    lock_input = False

    def __init__(self, character):
        self.character = character

    async def msg(self, text: Union[str, bytes]):
        """
        Send some text to the context character.

        Args:
            text (str or bytes): text to send.

        """
        await self.character.msg(text)

    async def move(self, context_path: str):
        """
        Move to another context.

        This is not supported for character contexts, the context stack
        should be used instead.

        """
        raise ValueError(
                "not supported in character contexts, "
                "use the context stack instead"
        )

    async def quit(self, verbose: Optional[bool] = True):
        """
        Quit the context.

        Args:
            verbose (bool, defaults True): should `leave` be called beforehand?

        """
        self.character.context_stack.remove(self)
        if verbose:
            await self.leave()
        await self.send_messages()

    def cannot_find(command: str) -> str:
        """
        Error to send when the command cannot be found.

        This is called when the command cannot be found in this context,
        or anywhere in the command stack.

        Args:
            command (str): the command.

        """
        return "that was an error, and it wasn't caught"
