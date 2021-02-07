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

"""Base class for commands."""

from contextlib import asynccontextmanager
from datetime import timedelta
from importlib import import_module
import inspect
from pathlib import Path
import traceback
from typing import Any, Callable, Dict, Optional, Sequence, Union

from command.args import ArgumentError, CommandArgs, Namespace
from command.log import logger
from tools.delay import Delay

NOT_SET = object()

class Command:

    """
    Base class for commands.

    Static commands are mostly defined and dynamically imported
    from the file system, from the 'command' directory and its
    sub-directories.

    A static command can have a name, inferred from the class
    name if not provided.  It can also have aliases, a command
    category and basic command permissions.  It's help entry is
    inferred from the command's docstring.

    Here's a very basic example.  Assuming you want to add the 'look'
    command, just create a file with the '.py' extension in the command
    package (it can be in a sub-package, for the sake of organization).

    ```python
    from command import Command, CommandArgs

    class Look(Command): # 'look' (lowercase class name) will be the name

        '''
        Look command, to look around you.

        Syntax:
            look [object]

        This command is used to look around you or look a specific object
        more in details.

        '''

        # If you're not happy with the default name, just provide a
        # class variable 'name' and set the command name to it.  You can
        # define the category in the 'category' class variable as a
        # string, and the command permissions, still as a string, in the
        # 'permissions' class variable.  If they're not defined,
        # these last two values will be searched in parent packages
        # following a capitalized convention (see below).
        args = CommandArgs()
        args.add_argument("object", optional=True)

        async def run(self, args):
            '''The command is executed.'''
            await self.msg("Ho, look!")
    ```

    If the `category` and/or `permissions` class variable aren't
    provided, they're automatically searched in the module and
    parent packages.  A `CATEGORY` variable is searched in this module
    and, if not found, in parent packages recursively.  Similarly,
    a `PERMISSIONS` variable is searched in the module and parent
    packages.  This system allows to easily organize commands.

    For instance, assuming you want to create commands that only the
    administrators should use:  you could create a directory called
    'admin' inside of the 'command' package.  In this new directory,
    add an `__init__.py` file.  Inside write the following:

    ```python
    CATEGORY = "Admin commands"
    PERMISSIONS = "admin"
    ```

    Then you can create a file per command as usual.  For instance,
    create a file 'services.py' that contains the following code:

    ```python
    from command import Command, CommandArgs

    class Services(Command):

        '''Command services, to look for active services in the game.'''

        # name will be 'services'
        # ...
    ```

    Because we haven't defined a `category` class variable, a
    `CATEGORY` top-level variable will be searched in the module
    itself.  Since we haven't defined one, it will be searched in the
    parent package (that is, in our 'command/admin/__init.py' file).
    In this file is our `CATEGORY` variable, so the 'services'
    command will have its category set to 'Admin commands'.  The same
    process applies for permissions.  Notice that you can always
    override this behavior should the need arise, but it makes
    organization much easier.

    """

    #name = "command name"
    #category = "command category"
    #permissions = "command permissions"
    args = CommandArgs()
    seps = " "
    alias = ()

    def __init__(self, character=None, sep=None, arguments=""):
        self.character = character
        self.sep = sep
        self.arguments = arguments

    @property
    def session(self):
        return self.character and self.character.session or None

    @property
    def db(self):
        """Return the attribute handler for command storage."""
        if (handler := getattr(self, "cached_db_handler", None)):
            return handler

        from data.handlers import AttributeHandler
        if self.character is None:
            raise ValueError("the character is not set, can't access attributes")

        handler = AttributeHandler(self.character)
        handler.subset = f"cmd.{self.layer}.{self.name}"
        self.cached_db_handler = handler
        return handler

    def __getstate__(self):
        state = dict(self.__dict__)
        state.pop("cached_db_handler", None)
        return state

    @classmethod
    def can_run(cls, character) -> bool:
        """
        Can the command be run by the specified character?

        Args:
            character (Character): the character to run this command.

        By default, check the command's permissions.  You can,
        however, override this method in individual commands
        to perform other checks.

        Returns:
            can_run (bool): whether this character can run this command.

        """
        if cls.permissions:
            return character.permissions.has(cls.permissions)

        return True

    def get_help(cls, character=None) -> str:
        """
        Return the help of a command, tailored for a character.

        If a character asks for this command help, the command
        permissions are checked beforehand.  It can be assumed
        the character is authorized to see this command at this
        point.  However, if the character isn't specified, there's
        no way to be sure she could execute the command, as she's
        not specified.  Handle this use case before calling
        `get_help` with no argument, as this is a rather special
        use case.

        Args:
            character (Character, optional): the character asking for help.

        Returns:
            help (str): the command help as a str.

        """
        return inspect.getdoc(cls)

    @classmethod
    def new_parser(self):
        """Simply return an empty command argument parser."""
        return CommandArgs()

    def parse(self, character: 'db.Character'):
        """Parse the command, returning the namespace or an error."""
        return type(self).args.parse(character, self.arguments)

    async def run(self, args):
        """
        Run the command with the provided arguments.

        The command arguments are first parsed through the command
        argument parser (see `command/args.py`), so that this method
        is only called if arguments are parsed correctly.

        Args:
            args (namespace): The correctly parsed arguments.

        The method signature is actually quite variable.  You can specify
        the keyword arguments for your command which helps to parse them.
        See 'admin/py.py' for instance.

        """
        await self.msg(f"Great!  You reached the command {self.name}.")

    def call_in(self, *args, **kwargs):
        """
        Schedule a callback to run in X seconds.

        Args:
            delay (int or float or timedelta): the delay (in seconds).
            callback (Callable): the callback.  It can be
                    a synchronous or asynchronous function.
        Additional positional or keyword arguments will be sent to the
        callback when it's time to execute it.

        """
        return Delay.schedule(*args, **kwargs)

    async def parse_and_run(self):
        """
        Parse and, if possible, run the command.

        This is a shortcut to first parse, then run the command
        asynchronously withint a try/except block to catch errors.

        """
        async with self.group_messages():
            try:
                result = self.parse(self.character)
                if isinstance(result, ArgumentError):
                    await self.msg(str(result))
                    return

                args = self.args_to_dict(result)
                await self.run(**args)
            except Exception:
                # If an administrator, sends the traceback directly
                if self.character and self.character.permissions.has("admin"):
                    await self.msg(traceback.format_exc(), raw=True)

                logger.exception(
                        f"An error occurred while parsing and running the "
                        f"{self.name} commnd:"
                )

    async def msg(self, text: str, raw: Optional[bool] = False):
        """
        Send the message to the character running the command.

        Args:
            text (str): text to send to the character.
            raw (bool, optional): if True, escape braces.

        """
        await self.character.msg(text, raw=raw)

    @asynccontextmanager
    async def group_messages(self):
        """Group messages, to use in an async with statement."""
        await type(self).condition.mark_as_running(self)
        try:
            yield
        finally:
            await type(self).condition.mark_as_done(self)

    @classmethod
    def extrapolate(cls, path: Path):
        """
        Extrapolate name, category and permissions if not set.

        This will entail looking into parent modules if needed.

        Args:
            path (pathlib.Path): path leading to the command.

        """
        # Try to find the command name
        if not hasattr(cls, "name"):
            cls.name = cls.__name__.lower()

        # Try to find the command category, permissions and layer
        if any(not hasattr(cls, missing) for missing in
                ("category", "permissions", "layer")):
            category, permissions, layer = cls._explore_for(path, (
                    "CATEGORY", "PERMISSIONS", "LAYER"))

            if not hasattr(cls, "category"):
                category = category or "General"
                cls.category = category

            if not hasattr(cls, "permissions"):
                permissions = permissions or ""
                cls.permissions = permissions

            if not hasattr(cls, "layer"):
                layer = layer or "static"
                cls.layer = layer

    @staticmethod
    def _explore_for(path: Path, names: Sequence[str]):
        """Explore for the given variable names."""
        values = [NOT_SET] * len(names)
        current = path
        while str(current) != '.':
            if current.parts[-1].endswith(".py"):
                current = current.parent / current.stem

            pypath = ".".join(current.parts)
            module = import_module(pypath)
            for i, name in enumerate(names):
                if values[i] is not NOT_SET:
                    continue

                value = getattr(module, name, NOT_SET)
                if value is not NOT_SET:
                    values[i] = value

            if not any(value is NOT_SET for value in values):
                return tuple(values)

            current = current.parent

        # Some values couldn't be found in parent directories
        for i, value in enumerate(values):
            if value is NOT_SET:
                values[i] = None

        return tuple(values)

    @classmethod
    def args_to_dict(cls, args: Namespace) -> Dict[str, Any]:
        """
        Return a dictionary based on the `run` arguments.

        The `run` method can have:
            An argument called `args` which contains the entire namespace.
            An argument for each namespace arguments.

        This class method will create a dictionary based on the
        expected arguments of the `run` method.

        Returns:
            args_as_dict (dict): the packed namespace as a dict.

        """
        to_dict = {}
        signature = inspect.signature(cls.run)
        parameters = [p for p in signature.parameters.values() if
                p.name != "self"]

        for parameter in parameters:
            if parameter.name == "args":
                to_dict["args"] = args
            else:
                value = getattr(args, parameter.name, NOT_SET)
                if value is NOT_SET:
                    default = parameter.default
                    if default is inspect._empty:
                        raise ValueError(
                                f"{cls}: the command requires the keyword "
                                f"argument {parameter.name!r}, but it's not "
                                "defined as a command argument and doesn't "
                                "have a default value in the method signature"
                        )

                    value = default
                to_dict[parameter.name] = value

        return to_dict
