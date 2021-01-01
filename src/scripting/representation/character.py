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

"""Character object representation.

Thie following class defines a wrapper around the character
objects, as they are used in the scripting.  This allows to
avoid accessing or modifying attributes on the character itself,
including calling methods of this class.  Rather, the object
representation describes what is allowed, what is publicly
available in a script when this object is manipulated.

"""

from data.character import Character as Represent
from data.character import VariableFormatter
from scripting.representation.abc import BaseRepresentation

class Character(BaseRepresentation):

    """Character object representation."""

    represent = Represent

    def __init__(self, script, character):
        super().__init__(script, character)
        self._character = character

    def _update(self, script, character):
        """Update this object representation."""
        self.script = script
        self.character = character

    async def msg(self, message: str):
        """
        Send the message to this character.

        Args:
            message (str): the message to send.

        Variables in the messages are read from the top-level
        namespace.  Thus, a script like this:

            number = 3
            character.msg("The number is: {number}")

        ... will send the following message to the character:

            The number is: 3

        Additionally, the syntax for pluralization also is supported:

            num_dogs = 2
            character.msg("I see {num_dogs} {num_dogs:dog/dogs} here."

        ... will send:

            I see 2 dogs here.

        """
        variables = self._script.top_level.attributes.copy()
        await self._character.msg(message, variables=variables)
