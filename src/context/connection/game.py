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

"""Game context, where commands can be entered.

This is the most important and used context.  Connected players go
in this context, where they can type game commands through which
most of their action is performed.

"""

from command.layer import StaticCommandLayer
from command.stack import CommandStack
from context.base import BaseContext

class Game(BaseContext):

    """Game context."""

    async def enter(self):
        """The session enters the context, check the character's location."""
        character = self.session.character
        location = character.storage.get("saved_location")
        if character.location is None:
            character.location = location

        await super().enter()

    async def greet(self):
        """Just display the character's location."""
        character = self.session.character
        if character.location:
            title = character.location.title
        else:
            title = "Unknown location... something's very wrong here!"

        return title + "\n\nHP: 100"

    async def input(self, command: str):
        """The character has entered something."""
        character = self.session.character
        command = character.command_stack.find_command(command)
        if isinstance(command, str):
            # Can't find the command, display the error
            await self.msg(command)
            return

        # Otherwise, parse the command
        args = command.parse()
        await command.run(args)
