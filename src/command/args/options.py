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

"""Options argument.

Options can follow different formats.  By default, options
are to be specified like this:
    option1 = text of the option option2 = other text

Short options can be added.  Spaces around the equal signs
are not mandatory.

"""

from collections import namedtuple
from typing import Any, Optional, Sequence, Union

from command.args.base import ArgSpace, Argument, ArgumentError, Result

_NOT_SET = object()

class Options(Argument):

    """Options class for argument."""

    name = "options"
    space = ArgSpace.UNKNOWN
    in_namespace = True

    def __init__(self, dest, optional=False, default=None):
        super().__init__(dest, optional=optional, default=default)
        self.options = []
        self.names = {}
        self.msg_unknown_option = "Unknown option: {option}"
        self.msg_mandatory_option = "This option is mandatory: {option}"

    def __repr__(self):
        return "[options]"

    def add_option(self, name: str, *names: Sequence[str],
            optional : Optional[bool] = True,
            default: Optional[Any] = _NOT_SET, dest: Optional[str] = None):
        """
        Add an option.

        Args:
            name (str): at least one name.  Several names are supported as additional posiitonal arguments.
            optional (bool, optional): whether this option is mandatory or optional.  If a default value is specified (see next argument), an option is optional.
            default (Any, optional): if not set, the option will use this default value.
            dest (str, optional): where to write this option
                    in the namespace?  By default, the option dest
                    will be its long name.

        """
        names = (name, ) + names
        if any([name in self.names for name in names]):
            raise ValueError("one of the name is already being used "
                    "by another option")

        option = Option(names, optional=optional, default=default, dest=dest)

        self.options.append(option)
        for name in names:
            self.names[name] = option

    def parse(self, character: 'db.Character', string: str, begin: int = 0,
            end: Optional[int] = None) -> Union[Result, ArgumentError]:
        """
        Parse the argument.

        Args:
            character (Character): the character running the command.
            string (str): the string to parse.
            begin (int): the beginning of the string to parse.
            end (int, optional): the end of the string to parse.

        Returns:
            result (Result or ArgumentError).

        """
        end = end or len(string)
        to_parse = string[begin:end]

        # Parse in backward
        end_pos = len(to_parse)
        equal_pos = to_parse.rfind("=", None, end_pos)
        parsed = {}
        options = {}
        while equal_pos != -1:
            # Check that the previous character isn't an equal sign too
            if equal_pos > 0 and to_parse[equal_pos - 1] == '=':
                equal_pos = to_parse.rfind("=", None, equal_pos - 1)
                continue

            # Look for the name
            begin_name = equal_pos

            # Remove the spaces between the equal sign and the name, if any
            while begin_name > 0:
                char = to_parse[begin_name - 1:begin_name]
                if not char.isspace():
                    break

                begin_name -= 1

            # Capture the name until the previous space
            while begin_name > 0:
                char = to_parse[begin_name - 1:begin_name]
                if char.isspace():
                    break

                begin_name -= 1

            # name is betwen thesee two positions
            name = to_parse[begin_name:equal_pos].strip()
            value = to_parse[equal_pos + 1:end_pos].strip().replace("==", "=")
            parsed[name] = value
            end_pos = begin_name
            equal_pos = to_parse.rfind("=", None, end_pos)

        # Match the parsed options
        for name, value in reversed(parsed.items()):
            option = self.names.get(name.lower())
            if option is None:
                return ArgumentError(self.msg_uknown_option.format(
                        option=name))

            options[option] = value

        # Browse the list of default options
        for option in self.options:
            if option in options.keys():
                continue

            # If it has a default value
            if option.default is not _NOT_SET:
                options[option] = option.default
                continue

            # But if it's mandatory,r aise an error
            if not option.optional:
                self.raise_error(self.msg_mandatory_option.format(
                        option=option.names))

        result = Result(begin=begin, end=end, string=string)
        result.options = options
        return result

    def add_to_namespace(self, result, namespace):
        """Add the parsed options directly to the namespace."""
        options = result.options
        for option, value in options.items():
            setattr(namespace, option.dest, value)


Option = namedtuple("Option", "names optional default dest")
