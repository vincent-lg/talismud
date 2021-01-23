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

"""Base class of all contexts.

A context is a "step" in the login process.  A context displays some
information and handles user input.  A simple context, the
message-of-the-day, is created whenever a session is createed.  This
context will greet the new session and display instructions to login.
From there, depending on user input, the task will be handed to a different
context (say, the creation of the username, for instance, or the password).

"""

from abc import ABCMeta, abstractmethod
import asyncio
from importlib import import_module
import inspect
from pathlib import Path
from textwrap import dedent
from typing import Optional, Union

from context.log import logger
import settings
from tools.delay import Delay

# Constants
CONTEXTS = {}

class BaseContext(metaclass=ABCMeta):

    """
    Class defining a context.

    Class attributes:
        text: a text that doesn't require further processing.  In case
              you want the text to change depending on session information,
              override the `greet` method instead.  Don't hesitate
              to use multiline strings, they will be dedent-ed
              (see `textwrap.dedent`).

    Instance attributes:
        session (Session): the session object.  You can use
                          `session.options` to access the session's
                          option handler which can be handy to store
                          information on the session itself.
                          This information will be available as long
                          as the session exists (that is, even if the
                          game stops and starts again, as long as the
                           session is maintained by the user).

    Methods:
        greet()            greet the user with some text.  The text
                           to be displayed should be returned (return
                           `None` to not send any text at all).
        enter()            The session first enters this context.  By
                           default, this method just calls `greet` and
                           sends its returned text to the session.  This
                           method is not called if the session already
                           is on this context without moving to another.
                           That's why you should always have a `text`
                           class variable or `greet` method that does return
                           some text, overriding `enter` isn't that
                           frequent, except to perform memory
                           operations on the session for instance.
        leave()            Called when the session is about to leave
                           this context to go to another.  By default,
                           this method does nothing.
        move(new_context)  Move the session to a new context.  The
                           current context's `leave` method will be called,
                           then the new context will be created with
                           the same session and its `greet` method will
                           be called.  You shouldn't override this method,
                           just use it.
        msg(text)          Send some text to the session.  This is just
                           a shortcut for `self.session.msg(text)`.
        refresh()          Called when the user asks for a refresh.  By
                           default, calls `greet` and send the result to
                           the session.  This method will also be called
                           by `enter` if not overridden.

    Contexts have a simple in-built command system.  Contexts can
    define methods that will be called when a user enters text that
    matches the method name.  For instance, if you want to react
    when the user enters "help", define a method called
    `input_help` in your context.  This method will be called
    ONLY if the user enters "help" or possibly "help something".
    In the second case, the argument ("something") will be passed
    to the `input_help` method.  So your `input_help` can be
    defined in two ways:

        async def input_help(self):

    OR

        async def input_help(self, args: str):

    Arguments will be passed to the method only if it asks for them
    (has a positional argument after `self`).  If the context can't
    find an `input_...` method matching user input, it will then
    call `input` and send the entire user input as argument.

    Don't override `handle_input`, just create `input_...` and
    `input` methods on the context.

    """

    pyname = "UNSET"
    prompt = ""
    text = ""

    def __str__(self):
        return self.pyname

    async def greet(self) -> Optional[str]:
        """
        Greet the session or character.

        This method is called when the session first connects to this
        context or when it calls for a "refresh".  If the context
        is simple, you don't need to override this method, just specify
        the `text` class variable.  If, however, you want to change
        the text based on session information, you can override
        this method.  Be sure to return the text to be sent to the
        session.  If you return `None`, no text will be sent, which
        might be confusing to the user.

        """
        return self.text

    async def refresh(self):
        """Refresh the context view."""
        await type(self).condition.mark_as_running(self)
        text = await self.greet()
        if text is not None:
            if isinstance(text, str):
                text = dedent(text.strip("\n"))

            await self.msg(text)

        await self.send_messages()

    async def enter(self):
        """
        The session or character first enters in this context.

        You can ovverride this method to do something when the session
        or character enters the context for the first time.

        """
        await type(self).condition.mark_as_running(self)
        await self.refresh()
        await self.send_messages()

    async def leave(self):
        """
        The session or character is about to leave this context.

        Override this method to perform some operations on the session
        or character when it leaves the context.

        """
        pass

    def get_prompt(self):
        """Return the prompt to be displayed for this context."""
        return self.prompt

    async def input(self, command: str):
        """
        What to do when no user input matches in this context.

        Args:
            command (str): the full user input.

        """
        await self.msg("What to do?")

    async def handle_input(self, user_input: str):
        """
        What to do when the user enters text in the context?

        Contexts have a simple in-built command system.  Contexts can
        define methods that will be called when a user enters text that
        matches the method name.  For instance, if you want to react
        when the user enters "help", define a method called
        `input_help` in your context.  This method will be called
        ONLY if the user enters "help" or possibly "help something".
        In the second case, the argument ("something") will be passed
        to the `input_help` method.  So your `input_help` can be
        defined in two ways:

            async def input_help(self):

        OR

            async def input_help(self, args: str):

        Arguments will be passed to the method only if it asks for them
        (has a positional argument after `self`).  If the context can't
        find an `input_...` method matching user input, it will then
        call `input` and send the entire user input as argument.

        Don't override `handle_input`, just create `input_...` and
        `input` methods on the context.

        Args:
            user_input (str): the user input.

        """
        await type(self).condition.mark_as_running(self)
        if " " in user_input:
            command, args = user_input.split(" ", 1)
        else:
            command, args = user_input, ""

        # Try to find an input_{command} method
        method = getattr(self, f"input_{command}", None)
        if method:
            # Pass the command argument if the method signature asks for them
            signature = inspect.signature(method)
            if len(signature.parameters) == 0:
                await method()
                await self.send_messages()
                return True

            await method(args)
            await self.send_messages()
            return True

        method = self.input
        res = await method(user_input)
        await self.send_messages()
        return res

    @abstractmethod
    async def move(self, context_path: str):
        """
        Move to a new context.

        You have to specify the new context as a Python path, like
        "connection.motd".  This path is a shortcut to the
        "context.connection.motd" module (unless it has been replaced
        by a plugin).

        Args:
            context_path (str): path to the module where the new context is.

        Note:
            Character contexts cannot be moved with this method.  Use
            the context stack on the character
            (`character.context_stack.add(...)` instead).

        """
        pass

    @abstractmethod
    async def msg(self, text: Union[str, bytes]):
        """
        Send some text to the context.

        Args:
            text (str or bytes): text to send.

        """
        pass

    async def send_messages(self):
        """
        Send all messages to the character.

        This will also send the context prompt, if it's active.

        """
        if self not in type(self).condition.running:
            return

        await type(self).condition.mark_as_done(self)

    @staticmethod
    def call_in(seconds, callback, *args, **kwargs):
        """Call a function in X seconds."""
        Delay.schedule(seconds, callback, *args, **kwargs)

def load_contexts(condition: asyncio.Condition,
        raise_exception: Optional[bool] = False):
    """
    Load the contexts dynamically.

    This function is called when the game starts.

    Args:
        condition (Condition): a condition object, to lock messaging.
        raise_exceptions (bool, defaults `False`): should an exception
                be raised when a context module cannot be loaded?

    """
    BaseContext.condition = condition
    from context.character_context import CharacterContext
    from context.session_context import SessionContext
    parent = Path()
    paths = (
        parent / "context",
    )

    for plugin in settings.PLUGINS:
        paths += (parent / plugin / "context", )

    exclude = (
        parent / "context" / "base.py",
        parent / "context" / "character_context.py",
        parent / "context" / "log.py",
        parent / "context" / "session_context.py",
        parent / "context" / "stack.py",
    )
    forbidden = (BaseContext, CharacterContext, SessionContext)

    # Search the context files
    logger.debug("Preparing to load all contexts...")
    loaded = 0
    for path in paths:
        for file_path in path.rglob("*.py"):
            if file_path in exclude or any(
                    to_ex in file_path.parents for to_ex in exclude):
                continue                                # Search for the module to begin

            if file_path.name.startswith("_"):
                continue

            # Assume this is a module containing ONE context
            relative = file_path.relative_to(path)
            pypath = ".".join(file_path.parts)[:-3]
            py_unique = ".".join(relative.parts)[:-3]

            # Try to import
            try:
                module = import_module(pypath)
            except Exception:
                logger.exception(
                        f"  An error occurred when importing {pypath}:")
                if raise_exception:
                    raise
                continue

            # Explore the module to try to import ONE context.
            NewContext = None
            for name, value in module.__dict__.items():
                if name.startswith("_"):
                    continue

                if (isinstance(value, type) and value not in forbidden
                        and issubclass(value, BaseContext)):
                    if NewContext is not None:
                        NewContext = ...
                        break
                    else:
                        NewContext = value

            if NewContext is None:
                logger.warning(f"No context could be found in {pypath}.")
                continue
            elif NewContext is ...:
                logger.warning(
                        "More than one contexts are present "
                        f"in module {pypath}, not loading any."
                )
                continue
            else:
                loaded += 1
                logger.debug(
                        f"  Load the context in {pypath} (name={py_unique!r})"
                )
                CONTEXTS[py_unique] = NewContext
                NewContext.pyname = py_unique

    s = "s" if loaded > 1 else ""
    was = "were" if loaded > 1 else "was"
    logger.debug(f"{loaded} context{s} {was} loaded successfully.")
