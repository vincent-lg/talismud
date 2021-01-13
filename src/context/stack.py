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

"""Command stack, to hold command layers and contexts."""

from pickle import dumps
from typing import Optional, Type, Union

from command.layer import CommandLayer, LAYERS
from context.base import BaseContext, CONTEXTS
from context.log import logger

class ContextStack:

    """
    Command stack, to hold command layers and contexts.

    A command stack contains contexts and command layers, with one of them
    being active.  The active context will receive a command entered
    by the character.  If a match isn't found, the command is looked
    into the following contexts until a match is found.  The last
    context in the stack gets to indicate an error occurred
    if a match wasn't found.

    The relationship between context and command layer is as follows:
    a context can hold a command layer ; if so, all commands are
    sent to this command layer.  A command layer is simply a way
    to organize commands and add them in bulk when the situation
    requires it.

    """

    def __init__(self, character=None):
        self.character = character
        self.contexts = []

    def __repr__(self):
        contexts = []
        for context in self.contexts:
            ret = ""
            if context.active:
                ret += "*"

            ret += str(context)
            contexts.append(ret)

        return f"<ContextStack {', '.join(contexts)}>"

    @property
    def active_context(self):
        """Return the active context."""
        return [context for context in self.contexts if context.active][0]

    def add_context(self, context_path: str,
            active: Optional[bool] = True):
        """
        Add a context to the command stack.

        This method allows to add a context to the command stack.
        If the added context only holds a command layer, it is preferable
        to call `add_command_layer` instead.

        Args:
            context_path (str): the Python path to the context.
            active (bool, opt): should this context be active?

        Note: a new context will always be active if there's no
        active context on the stack.        context is active in this stack?

        """
        NewContext = CONTEXTS[context_path]
        context = NewContext(self.character)

        if active or not any(c.active for c in self.contexts):
            context.active = True
            for other in self.contexts:
                other.active = False

        self.contexts.insert(0, context)
        self._save()
        return context

    def add_command_layer(self, layer: Union[str, CommandLayer,
            Type[CommandLayer]], active: Optional[bool] = True):
        """
        Add a new command layer to the stack.

        Args:
            layer (str or CommandLayer or subclass of CommandLayer):
                    the command layer to add.  It can either be a
                    string (the command layer name), a `CommandLayer`
                    instance (a prebuilt command layer) or a subclass
                    of `CommandLayer`.  In the latter case, `load`
                    is called on this command layer class.
            active (bool, opt): should this context be active?

        Note: a new context will always be active if there's no
        active context on the stack.        context is active in this stack?

        """
        if isinstance(layer, str):
            layer = LAYERS[layer]

        if isinstance(layer, type) and issubclass(layer, CommandLayer):
            layer = layer.load(self.character)

        context = self.add_context("connection.layer", active=active)
        context.layer = layer
        self._save()
        return layer

    def remove(self, context: BaseContext):
        """
        Remove the specified context.

        Args:
            context (BaseContext): the context to remove.

        If the context to remove was active, move the active flag to the
        next context... and if not possible, to the previous one.

        Raises:
            ValueError: if trying to remove the last (static context).
                    This cannot be done and shouldn't be attempted.

        """
        index = self.contexts.index(context)
        if index == len(self.contexts) - 1: # This is the last context
            raise ValueError("cannot remove the last context")

        if context.active:
            if index < len(self.contexts) - 1:
                self.contexts[index + 1].active = True
            elif index > 0:
                self.contexts[index - 1].active = True

        self.contexts.remove(context)
        self._save()

    def remove_context(self, context_path: str, **kwargs):
        """
        Remove the specified context.

        The first argument should be the Python path to the context.
        The next arguments should be keyword arguments, used to filter
        down the context to remove.  A comparison on attributes is done
        on the context.  Only one context is removed.

        Args:
            context_path (str): the path to the context to remove.

        Additional keyword arguments can be specified to filter down
        the list of contexts to remove.

        Note:
            This method will prevent removing the last context, which
            should always be the static context.

        """
        for i, context in enumerate(self.contexts[:-1]):
            if context.ppath == context_path:
                # The Python path is good, now filter it down
                valid = True
                for name, value in kwargs.items():
                    real = getattr(context, name, ...)
                    if real != value:
                        valid = False
                        break

                if not valid:
                    continue

                self.contexts.remove(context)

                # If the context was active, place the active flag
                # on the previous context, if any, or the next if none.
                if context.active:
                    if i > 0:
                        self.contexts[i - 1].active = True
                    else:
                        self.contexts[i].active = True
                self._save()
                return context

        raise ValueError(
                f"cannot find the context {context_path} with the "
                "specified arguments"
        )

    def remove_command_layer(self, layer: str, **kwargs):
        """
        Remove the given command layer.

        Args:
            layer (str): the command layer's name to remove.
            Additional keyword arguments can be used to filter down
            the list of contexts to remove.

        """
        self.remove_context("connection.layer", layer_name=layer, **kwargs)

    async def find_command(self, command: str):
        """
        Find a command, asking individual contexts.

        Args:
            command (str): the entered command.

        """
        # Find the first active context
        actives = [(i, context) for i, context in enumerate(self.contexts)
                if context.active]
        if not actives:
            # There's no active context.  This is definitely a bug.
            logger.error(
                    "There's no active context in the stack for "
                    f"{self.character}, this should never happen."
            )
            return

        index, active = actives[0]

        # TODO: handle the < and > to move along contexts.
        while True:
            match = await active.handle_input(command)
            if match:
                return match

            # Push to the next context, if allowed
            if not active.lock_input:
                index += 1
                if index >= len(self.contexts):
                    break
                else:
                    active = self.contexts[index]
            else:
                break

        # At this point, a match hasn't been found
        msg = active.cannot_find(command)
        if msg:
            await active.msg(msg)

    def _save(self):
        """Save the modifications to the command stack in the character."""
        if self.character:
            self.character.binary_context_stack = dumps(self)
