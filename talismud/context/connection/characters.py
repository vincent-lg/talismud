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

"""Display the list of characters for this account."""

from textwrap import dedent

from context.base import BaseContext
from data import Character
import settings

class Characters(BaseContext):

    """Context do display the account's characters."""

    async def greet(self):
        """Display the chaqracter's screen."""
        account = self.session.account
        screen = dedent(f"""
            Welcome to your account, {account.username}!

            You can select your characters here.  Enter a number to
            play one of these characters or the letter 'c' to create a new one.

            Available characters:
        """.strip("\n"))

        for i, character in enumerate(
                account.characters.sort_by(Character.created_on)):
            screen += f"\n  {i + 1} to play {character.name}"

        screen += "\n\n" + dedent("""
            Type 'c' to create a new character.
        """.strip("\n"))

        return screen

    async def input_c(self):
        """The player has entered 'c'."""
        await self.move("character.name")

    async def input(self, command: str):
        """Expecting a character number."""
        account = self.session.account
        command = command.lower().strip()
        for i, character in enumerate(
                account.characters.sort_by(Character.created_on)):
            if str(i + 1) == command:
                self.session.storage["character"] = character
                await self.move("connection.login")
                return

        await self.msg("Invalid command.")
