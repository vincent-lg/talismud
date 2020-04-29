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

"""Command stack, to hold command layers."""

from pickle import dumps
from typing import Optional, Type, Union

from command.layer import CommandLayer

class CommandStack:

    """
    Command stack, to hold command layers.

    A command stack contains command layers, with one active command
    layer.  The active command layer will receive a command entered
    by the character.  If a match isn't found, the command is looked
    into next command layers until a match is found.  The last
    command layer in the stack gets to indicate an error occurred
    if a match wasn't found.

    """

    def __init__(self, character=None):
        self.character = character
        self.command_layers = []

    def add_layer(self, layer: Union[CommandLayer, Type[CommandLayer]],
            active: Optional[bool] = True):
        """
        Add a new command layer to the stack.

        Args:
            layer (CommandLayer or subclass of CommandLayer):
                    the command layer to add.  It can either be a
                    `CommandLayer` instance (a prebuilt command layer)
                    or a subclass of `CommandLayer`.  In the latter
                    case, `load` is called on this command layer class.

        The command layer is set to the active state, if there's
        no active command layer in the stack.

        """
        if issubclass(layer, CommandLayer):
            layer = layer.load(self.character)
        if active or not any(l.active for l in self.command_layers):
            layer.active = True
            for other in self.command_layers:
                other.active = False

        self.command_layers.insert(0, layer)
        self._save()

    def remove_layer(self, layer: CommandLayer):
        """
        Remove the given command layer.

        Args:
            layer (CommandLayer): the command layer to remove.

        No error is raised even if the layer isn't found in the stack.

        """
        try:
            index = self.command_layers.index(layer)
        except ValueError:
            return

        if layer.active: # Transfer the active status to another layer
            if index < 0: # ... to the previous layer in the stack
                before = self.command_layers[index - 1]
                before.active = True
            elif len(self.command_layers) > 1: # ... to the next layer
                next = self.command_layers[index + 1]
                next.active = True

        self.command_layers.remove(layer)
        self._save()

    def find_command(self, command: str):
        """
        Find a command, asking individual layers.

        Args:
            command (str): the entered command.

        """
        layers = list(self.command_layers)
        while layers and not layers[0].active:
            del layers[0]

        if not layers:
            return

        last = None
        for layer in layers:
            last = layer
            if match := layer.find_command(command):
                return match

        if last:
            return last.cannot_find(command)

    def _save(self):
        """Save the modifications to the command stack in the character."""
        if self.character:
            self.character.db_command_stack = dumps(self)
