# Copyright 2018 Simon Davy
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""Service to execute scripts interactively."""

import traceback
import sys

from data.character import Character
from scripting.exceptions import NeedMore
from scripting.script import Script

class Scripting:

    """Slight modification of the interactive console for TalisMUD."""

    def __init__(self):
        self.script = Script()
        self.output = ""

    def write(self, data):
        """Write stdout/stderr data."""
        self.output += data

    async def push(self, code):
        """Push the code."""
        write = sys.stdout.write
        self.output = ""
        sys.stdout.write = self.write

        # Add default variables
        self.script.set_default_variables(character=Character.select().first())

        # Add the code as tokens
        try:
            self.script.add_tokens(code)
        except NeedMore:
            return True
        except Exception:
            self.output = traceback.format_exc()
            self.script.clear()
            return False

        # Generate the Abstract Syntax Tree (AST)
        try:
            if not await self.script.generate_AST():
                raise NeedMore
        except NeedMore:
            return True
        except Exception:
            self.script.clear()
            self.output = traceback.format_exc()
            return False

        # Generate the assembly
        try:
            await self.script.generate_assembly()
        except Exception:
            self.script.clear()
            self.output = traceback.format_exc()
            return False

        # Check types
        try:
            await self.script.check_types()
        except Exception:
            self.script.clear()
            self.output = traceback.format_exc()
            return False

        # Execute the script
        try:
            await self.script.execute()
        except Exception:
            self.script.clear()
            self.output = traceback.format_exc()
            return False

        # Get the last value in the stack
        val = self.script.empty_stack()
        if val is not None:
            print(val)

        self.script.clear()
        sys.stdout.write = write
        return False
