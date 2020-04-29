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

"""Abstract class for command layers."""

from importlib import import_module
from pathlib import Path
from typing import Optional

from command.base import Command, logger

class CommandLayer:

    """
    Abstract command layer.

    A command layer holds a set of commands with a given priority
    in the command stack.  A character executing commands has a
    default command list, contained in a single layer.  Additional
    layers might be required sometimes, in order to control NPCs for
    instance, where the player has access to two command layers: the
    NPC's and his player character's.  The player can move in the stack
    to change the active command layer. The active command layer always
    gets precedence on commands that are executed.  If the active
    command layer cannot find the command that the character entered,
    the next command layer in the stack is called and given the
    command.  If it fails it tries to find the command in the next
    layer and so on.  The last layer gets to indicate no matching
    command was found.  Command layers can prevent commands from
    going to the next layer, however.

    """

    name = "unknown"# Command layer name, can be a property
    active = False # The active command context
    propagate = True # Non-matching commands can propagate to the next layer

    def __init__(self, character=None):
        self.character = character
        self.commands = []

    def find_command(self, command: str) -> Optional[Command]:
        """
        Try to find the command based on its name.

        Returns either the matching command, or `None` if not found.

        Args:
            name (str): the command name.

        Returns:
            match (Command or None): the matching command.

        """
        # If the character is specified, check permissions
        character = self.character
        seps = {sep: () for comm in self.commands for sep in comm.seps}
        for sep in seps.keys():
            try:
                before, after = command.split(sep, 1)
            except ValueError:
                before = command
                after = ""

            seps[sep] = (before, after)

        logger.debug(f"Seps: {seps}")
        for command in self.commands:
            logger.debug(f"Test {command.name}, seps={command.seps!r}")
            for sep in command.seps:
                before, after = seps[sep]
                logger.debug(f"Test {before!r} == {command.name!r}")
                if before == command.name:
                    if character and not command.can_run(character):
                        continue

                    return command(character, sep, after)

        return None

    def cannot_find(self, command) -> str:
        """Return the message to be displayed when the command cannot be found."""
        return f"Cannot find the command '{command}'."

    @classmethod
    def load(self, character):
        """Load the command layer for this character."""
        return cls(character)


class StaticCommandLayer(CommandLayer):

    """
    The static, all important, always last command layer.

    This command layer contains almost all game commands, like 'quit'
    or 'say'.  It is added on all characters that want to execute a
    command, although it is not always persisted.  This command layer
    should always be the last in a command stack.

    This layer will load its commands from the file system and look
    for commands in the 'command' directory, avoiding files that
    are used by TalisMUD itself to focus on dynamically importing
    others.

    """

    name = "static"

    def __getstate__(self):
        """Return what to pickle."""
        to_save = dict(self.__dict__)
        del to_save["commands"]
        return to_save

    def __setstate__(self, saved):
        """Unpickle serialized layer."""
        self.__dict__.update(saved)
        layer = self.load(self.character)
        self.commands = layer.commands

    @classmethod
    def load(cls, character):
        """Load the static layer from the file system."""
        layer = cls(character)
        parent_dir = Path("command")
        exclude = [
            parent_dir / "args.py",
            parent_dir / "base.py",
            parent_dir / "layer.py",
            parent_dir / "stack.py",
        ]

        for path in parent_dir.rglob("*.py"):
            if path in exclude:
                continue

            if path.name.startswith("_"):
                continue

            # Assume this is a module containing a command
            pypath = ".".join(path.parts)[:-3]
            module = import_module(pypath)

            # Explore the module for command classes
            for key, value in module.__dict__.items():
                if value is not Command and isinstance(value,
                        type) and issubclass(value, Command):
                    command = value.extrapolate(path)
                    layer.commands.append(command)
        return layer
