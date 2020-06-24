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

"""Base class for commands."""

from importlib import import_module
from pathlib import Path
from typing import Any

from logbook import FileHandler, Logger

from command.args import CommandArgs

NOT_SET = object()

# Logger
logger = Logger()
file_handler = FileHandler("logs/commands.log",
        encoding="utf-8", level="DEBUG", delay=True)
file_handler.format_string = (
        "{record.time:%Y-%m-%d %H:%M:%S.%f%z} [{record.level_name}] "
        "{record.message}"
)
logger.handlers.append(file_handler)

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

        async def call(self, args):
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

    Becasue we haven't defined a `category` class variable, a
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

    def __init__(self, character=None, sep=None, arguments=""):
        self.character = character
        self.sep = sep
        self.arguments = arguments

    @property
    def session(self):
        return self.character and self.character.session or None

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

    def parse(self):
        """Parse the command, returning the namespace or an error."""
        return type(self).args.parse(self.arguments)

    async def run(self, args):
        """
        Run the command with the provided arguments.

        The command arguments are first parsed through the command
        argument parser (see `command/args.py`), so that this method
        is only called if arguments are parsed correctly.

        Args:
            args (namespace): The correctly parsed arguments.

        """
        await self.msg(f"Great!  You reached the dcommand {self.name}.")

    async def msg(self, text: str):
        """
        Send the message to the character running the command.

        Args:
            text (str): text to send to the character.

        """
        await self.character.msg(text)

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

        # Try to find the command category
        if not hasattr(cls, "category"):
            cls.category = cls._explore_for(path, "CATEGORY",
                    default="General")

        # Look for the command permissions
        if not hasattr(cls, "permissions"):
            cls.permissions = cls._explore_for(path, "PERMISSIONS", default="")

        return cls

    @staticmethod
    def _explore_for(path: Path, name: str, default: Any):
        """Explore for the given variable name."""
        pypath = ".".join(path.parts)[:-3]
        module = import_module(pypath)
        value = getattr(module, name, NOT_SET)
        if value is not NOT_SET:
            return value

        # Import parent directories
        rindex = 1
        while rindex < len(path.parts) - 1:
            pypath = ".".join(path.parts[:-rindex])
            module = import_module(pypath)
            value = getattr(module, name, NOT_SET)
            if value is not NOT_SET:
                return value
            rindex += 1

        return default
