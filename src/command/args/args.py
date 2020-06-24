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

"""Command arguments."""

from typing import Optional, Union

from command.args.base import ArgSpace, ARG_TYPES
from command.args.error import ArgumentError
from command.args.namespace import Namespace
from command.args.result import Result

class CommandArgs:

    """
    Command arguments, to be parsed BEFORE the command is called.

    Command arguments can be seen as a parser, somewhat identical
    to the one defined in the `argparse` module.  It has a focus on the
    order of argument parsing, however, and can be configured in
    an incremental way.

    For instance, if you want a command to take an optional argument
    which can be a number, and then a required argument that can be
    an object name, you would do something like this:

    ```python
    class MyCommand(Command):

        args = CommandArgs()
        args.add_argument("number", optional=True)
        args.add_argument("object")
    ```

    This parser will work for:

        '5 apples'
        '1 gold piece'
        'sword'

    The parser will check for two things:

    1.  Does the command argument begins with a number?  If so,
        feed it to the first argument (number).  If not,
        go on.
    2.  It checks that there is a word in the command arguments.  This
        word, the object name, will be checked against the valid
        object names the character has.  In other words, if the
        character entered an invalid objedct name, the command
        will not even be executed.

    Valid methods on the command arguments parser are:
        add_argument: add an argument.
        add_branch: add a branch in which arguments can be set.
        add_keyword: add a keyword argument.
        add_delimiter: add a delimiter argument.

    Adding a keyword or a delimiter is so common a task that helper
    methods have been created to do so, but you can also use `add_argument`
    to add these argument types.

    """

    def __init__(self):
        self.arguments = []

    def add_argument(self, arg_type: str, dest: Optional[str] = None,
            optional=False, **kwargs):
        """
        Add a new argument to the parser.

        Args:
            arg_type (str): the argument type.
            dest (str, optional): the attribute name in the namespace.
            optional (bool, optional): is this argument optional?

        Additional keyword arguments are sent to the argument class.

        """
        arg_class = ARG_TYPES.get(arg_type)
        if arg_class is None:
            raise KeyError(f"invalid argument type: {arg_type!r}")

        dest = dest or arg_type
        argument = arg_class(dest, optional=optional, **kwargs)
        self.arguments.append(argument)

    def parse(self, arguments: str) -> Union[Namespace, ArgumentError]:
        """
        Try to parse the command arguments.

        This method returns either a parsed namespace containing the parsed arguments, or an error representing by `ArgumentError`.

        Args:
            arguments (str): the unparsed arguments as a string.

        Returns:
            result (`Namespace` or `ArgumentError`): the parsed result.

        """
        results = [None] * len(self.arguments)

        # Parse arguments with definite size
        fixed = [arg for arg in self.arguments if
                arg.space is not ArgSpace.UNKNOWN]
        for arg in fixed:
            i = self.arguments.index(arg)
            result = arg.parse(arguments, 0)
            results[i] = result

        # Parse other arguments
        begin = 0
        for i, arg in enumerate(self.arguments):
            result = results[i]
            if result:
                begin = result.end
                continue

            # If result is None, we need to delimit the argument
            if i == len(self.arguments) - 1: # That is the last argument
                result = arg.parse(arguments, begin)
                results[i] = result
                continue

            # If there's a result for the next argument, use its limit
            next_result = results[i + 1]
            if next_result:
                result = arg.parse(arguments, begin, next_result.begin)
                results[i] = result
                continue

            # Otherwise, that's an error
            raise ValueError(
                f"{arg!r} isn't the last argument, yet the nex argument "
                f"in line ({self.arguments[i + 1]!r}), cannot be parsed.")

        # Create the namespace
        namespace = Namespace()
        for arg, result in zip(self.arguments, results):
            if not arg.in_namespace:
                continue

            setattr(namespace, arg.dest, arguments[result.begin:result.end])

        return namespace
