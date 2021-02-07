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


"""Context to create a Python console in-game, for administrators.

To use it, an administrator should type the `py` command with
no argument.  The Python console allows her to type Python code,
including on several lines (Python blocks, like for loops or
if statements) and see the result.  The display is to be pretty
close from what one would obtain in a Python console.

"""

from code import InteractiveConsole
from io import StringIO
import pickle
import sys

from context.character_context import CharacterContext
from data.base import db

class PythonConsole(CharacterContext):

    """Context to simulate a Python console."""

    text = """
            TalisMUD Python console.
            Python {version} on {platform}.

            Type `q` to leave this console and go back to the game.

            You can also use these variables (plus any you create):
                self: the character calling this Python console.
                db: the database endpoint.
    """

    def __init__(self, character):
        super().__init__(character)
        self.buffer = ""
        self.console = None
        self.completed = True
        self.variables = {
                "self": self.character,
                "db": db,
        }

    def __getstate__(self):
        """Do not save the console."""
        to_save = dict(self.__dict__)
        _ = to_save.pop("console", None)
        variables = to_save["variables"]

        # Save only the variables that can be pickled
        for key, value in tuple(variables.items()):
            try:
                _ = pickle.dumps(value)
            except Exception:
                _ = variables.pop(key, None)
        return to_save

    async def greet(self) -> str:
        """Return the text when greeting the character in this context."""
        return self.text.format(version=sys.version, platform=sys.platform)

    async def leave(self):
        """Leave this context."""
        await self.msg("Closing the Python console.")

    async def input_q(self):
        """When the user enters 'q', quit this conext."""
        await self.quit()

    async def input(self, line: str):
        """Handle user input."""
        # Create a console, if there's none
        if getattr(self, "console", None) is None:
            self.console = InteractiveConsole(self.variables)
            # Push the buffer
            self.console.push(self.buffer)

        if self.buffer:
            self.buffer += "\n"
        self.buffer += line

        # Wrap the standard output and error in a StringIO
        out = StringIO()
        stdout, stderr = sys.stdout, sys.stderr
        sys.stdout = out
        sys.stderr = out

        # Try to execute the line
        self.completed = True
        self.console.locals.update({
                "db": db,
        })
        more = self.console.push(line)
        sys.stdout = stdout
        sys.stderr = stderr
        if more:
            self.completed = False
        else:
            self.buffer = ""

        prompt = ">>>" if self.completed else "..."
        out.seek(0)
        await self.msg(f"{out.read()}")

        # Force-save the context
        self.character.context_stack._save()
        return True

    def get_prompt(self):
        """Return the prompt to be displayed."""
        return ">>>" if self.completed else "..."
