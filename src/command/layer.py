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

"""Abstract class for command layers."""

import asyncio
from collections import defaultdict
from importlib import import_module
from pathlib import Path
from typing import Dict, Optional

from command.base import Command, logger
from command.log import logger
from command.special.exit import ExitCommand
import settings

# Constants
COMMANDS_BY_LAYERS = defaultdict(dict)
LAYERS = {}

class MetaCommandLayer(type):

    """Metaclass for command layers."""

    def __init__(cls, cls_name, bases, dct):
        if (name := cls.name):
            LAYERS[name] = cls


class CommandLayer(metaclass=MetaCommandLayer):

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

    name = "" # Command layer unique name

    def __init__(self, character=None):
        self.character = character
        self.commands = []

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

    def handle_input(self, command: str) -> Optional[Command]:
        """
        Handle the user input in this layer.

        By defaut, looks in the command layer's list of commands.
        It is possible to override this behavior however, to handle
        more custom commands (or even ignore the list of commands
        in this command layer).

        Args:
            command (str): the entered command.

        Returns:
            command (Command or None): the processed command.
                    Returning `None` means "not found, keep on
                    exploring other command layers, if appropriate".

        """
        return self.find_command(command)

    def find_command(self, command: str) -> Optional[Command]:
        """
        Try to find the command based on its name.

        Returns either the matching command, or `None` if not found.

        Args:
            name (str): the command name.

        Returns:
            match (Command or None): the matching command.

        """
        character = self.character
        seps = {sep: () for comm in self.commands for sep in comm.seps}
        for sep in seps.keys():
            try:
                before, after = command.split(sep, 1)
            except ValueError:
                before = command
                after = ""

            seps[sep] = (before, after)

        for command in self.commands:
            aliases = command.alias
            if isinstance(aliases, str):
                aliases = (aliases, )

            for sep in command.seps:
                before, after = seps[sep]
                if before == command.name or before in aliases:
                    if character and not command.can_run(character):
                        continue

                    return command(character, sep, after)

        return None

    def cannot_find(self, command: str) -> str:
        """
        Return the message to be displayed when the command cannot be found.

        Args:
            command (str): the entered command.

        Returns:
            message (str): the message to send to the character.

        """
        return f"Cannot find the command '{command}'."

    def load_commands(self):
        """
        Load the commands for this command layer.

        Usually you don't need to override this in your dynamic command
        layer.  However, if you want to add other, non-dynamic
        commands to your command layer, you can do so here.
        The added commands should find themselves in the list
        (`self.commands`), and should inherit the `Command` class,
        or be close enough (duck-typing).

        """
        self.commands = list(COMMANDS_BY_LAYERS.get(self.name, {}).values())

    @classmethod
    def load(cls, character):
        """Load the command layer for this character."""
        layer = cls(character)
        layer.load_commands()
        return layer


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

    def handle_input(self, command: str) -> Optional[Command]:
        """
        Test exits, then try to find the command based on its name.

        Args:
            command (str): the entered command.

        Returns:
            command (Command or None): the processed command.
                    Returning `None` means "not found, keep on
                    exploring other command layers, if appropriate".

        Note:
            Test exits if there's a valid character before testing
            out commands.

        """
        if (character := self.character):
            location = character.location
            exits = location.exits
            if (exit := exits.match(character, command)):
                return ExitCommand(character, exit)

        return self.find_command(command)

def load_commands(condition: asyncio.Condition,
        raise_exception: Optional[bool] = False):
    """
    Load all commands dynamically.

    This should be called once, when the game starts.  It will actively load commands (in installed plugins, as well).

    It will write the result in the `COMMANDS_BY_LAYERS` dicitonary,
    where the key is the command layer name (like 'static') and
    the value is a list of commands in this layer.

    Args:
        condition (Condition): the condition to synchronize messaging.
        raise_exception (bool, optional): raise an exception in case of error.

    """
    Command.condition = condition
    parent_dir = Path("command")
    exclude = [
        parent_dir / "args",
        parent_dir / "special",
        parent_dir / "base.py",
        parent_dir / "log.py",
        parent_dir / "layer.py",
    ]

    can_contain = (parent_dir, )
    plugins_path = Path("plugins")
    can_contain += tuple(plugins_path / name / "command" for name in
            settings.PLUGINS)
    logger.debug("Loading the commands...")
    how_many = 0
    for parent in can_contain:
        for path in parent.rglob("*.py"):
            if path in exclude:
                continue

            if any(to_ex in path.parents for to_ex in exclude):
                continue

            if path.name.startswith("_"):
                if path.stem != "__init__": # No point in logging __init__ files
                    logger.debug(f"  The commands in {path} are ignored.")
                continue

            # Assume this is a module containing a command
            relative = path.relative_to(parent)
            pypath = ".".join(path.parts)[:-3]

            # Try to import
            try:
                module = import_module(pypath)
            except Exception:
                logger.exception("  An error occurred when "
                        f"importing {pypath}")
                if raise_exception:
                    raise

                continue

            # Explore the module for command classes
            cmds_in_module = 0
            for key, value in module.__dict__.items():
                if value is not Command and isinstance(value,
                        type) and issubclass(value, Command):
                    command = value
                    command.extrapolate(path)
                    COMMANDS_BY_LAYERS[command.layer][command.name] = command
                    logger.debug(f"  Succesfully loaded "
                            f"{command.__module__}.{command.__name__} "
                            f"(layer={command.layer})")
                    cmds_in_module += 1
                    how_many += 1

            if cmds_in_module == 0:
                logger.warning("  No command was found in "
                        f"the {pypath} module")

    s = "s" if how_many > 1 else ""
    were = "were" if how_many > 1 else "was"
    logger.debug(f"{how_many} command{s} {were} succesfully loaded")

def find_command(name: str, layer: Optional[str] = "static"):
    """
    Find and return a command class or None.

    Args:
        name (str): the name of the command.
        layer (str, optional): the optional name of the layer.  If not
                set, only search in 'static'.  If set to 'None', search
                in every layer.

    Returns:
        command (command class or None): the command class, if found,
                else None.

    Raises:
        ValueError if the command layer cannot be found.

    """
    if layer is None:
        layers = COMMANDS_BY_LAYERS.values()
    else:
        filter = COMMANDS_BY_LAYERS.get(layer)
        if filter is None:
            raise ValueError("unknown command layer: {layer!r}")

        layers = [filter]

    for layer in layers:
        command = layer.get(name)
        if command is not None:
            return command

    return None # Explicit is better than implicit

def filter_can_run(commands: Dict[str, Command],
        character: 'Character') -> Dict[str, Command]:
    """
    Return the filtered dictionary of commands the character can run.

    Args:
        commands (dict): a dictionary of commands.
        character (Character): the character to test.

    Returns:
        allowed (Dict): the dicitonary of allowed commands.

    """
    return {name: command for name, command in commands.items()
            if command.can_run(character)}
