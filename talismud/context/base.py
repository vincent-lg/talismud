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

"""Base class of all contexts.

A context is a "step" in the login process.  A context displays some
information and handles user input.  A simple context, the
message-of-the-day, is created whenever a session is createed.  This
context will greet the new session and display instructions to login.
From there, depending on user input, the task will be handed to a different
context (say, the creation of the username, for instance, or the password).

"""

from importlib import import_module
import inspect
from pathlib import Path
from textwrap import dedent
from typing import Optional, Union

from data import Delay

class BaseContext:

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
                          `session.storage` to access the session's
                          storage handler which can be handy to store
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

    text = ""

    def __init__(self, session):
        self.session = session

    async def greet(self) -> Optional[str]:
        """
        Greet the session.

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
        text = await self.greet()
        if text is not None:
            if isinstance(text, str):
                text = dedent(text.strip("\n"))

            await self.session.msg(text)

    async def enter(self):
        """
        The session first enters in this context.

        You can ovverride this method to do something when the session
        enters the context for the first time.

        """
        await self.refresh()

    async def leave(self):
        """
        The session is about to leave this context.

        Override this method to perform some operations on the session
        when it leaves the context.

        """
        pass

    async def move(self, context_path: str):
        """
        Move to a new context.

        You have to specify the new context as a Python path, like
        "connection.motd".  This path is a shortcut to the
        "context.connection.motd" module and then a context will be
        searched in this module.  You don't have to specify the "context"
        part of the Python path, as it will be inferred.

        Args:
            context_path (str): path to the module where the new context is.

        """
        NewContext = self.find_context(context_path)
        new_context = NewContext(self.session)
        await self.leave()
        self.session.context = new_context
        await new_context.enter()

    async def msg(self, text: Union[str, bytes]):
        """
        Send some text to the context session.

        Args:
            text (str or bytes): text to send.

        """
        await self.session.msg(text)

    @staticmethod
    def find_context(context_path):
        """Find and return the context in the specified module."""
        # Search for the module to begin
        parts = context_path.split(".")
        parts[-1] += ".py"
        possible_paths = (
            Path().joinpath("context", *parts),
            Path().joinpath(*parts),
        )

        path = None
        for possible in possible_paths:
            if possible.exists():
                path = possible
                break

        if path is None:
            possible_paths = ", ".join([str(possible) for possible in
                    possible_paths])
            raise ModuleNotFoundError(
                    f"can't find {context_path!r} to import, tried "
                    f"{possible_paths}"
            )

        # Try to import the path
        pypath = ".".join(path.parts)
        pypath = pypath[:-3]

        # Try to import the module
        module = import_module(pypath)

        # The context should be a subclass from BaseContext
        NewContext = None
        for key, value in module.__dict__.items():
            try:
                if value is not BaseContext and issubclass(value, BaseContext):
                    NewContext = value
                    break
            except TypeError:
                continue

        if NewContext is None:
            raise ValueError(
                    f"cannot find the context class in {pypath}, "
                    "no subclass of `BaseContext` defined"
            )

        return NewContext

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
        try:
            command, args = user_input.split(" ", 1)
        except ValueError:
            command, args = user_input, ""

        # Try to find a input_{command} method
        method = getattr(self, f"input_{command}", None)
        if method:
            # Pass the command argument if the method signature asks for them
            signature = inspect.signature(method)
            if len(signature.parameters) == 0:
                return await method()

            return await method(args)

        method = self.input
        signature = inspect.signature(method)
        if len(signature.parameters) == 0:
            return await method()

        return await method(user_input)

    async def input(self, command: str):
        """
        What to do when no user input matches in this context.

        Args:
            command (str): the full user input.

        """
        await self.msg("What to do?")

    @staticmethod
    def call_in(seconds, callable, *args, **kwargs):
        """Call a function in X seconds."""
        Delay.call_in(seconds, callable, *args, **kwargs)
