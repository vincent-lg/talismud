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

"""Number argument.

This argument just consists of a single number, either int or float.

"""

from typing import Optional, Union

from command.args.base import ArgSpace, Argument, ArgumentError, Result

class Number(Argument):

    """Number class for argument."""

    name = "number"
    space = ArgSpace.WORD
    in_namespace = True

    def __init__(self, dest, optional=False, default=None):
        super().__init__(dest, optional=optional, default=default)
        self.min_limit = 1
        self.max_limit = None

        # Messages
        self.msg_invalid_number = "'{number}' isn't a valid number."
        #msg_low_number and msg_high_number can also be defined

    def __repr__(self):
        return "<Number>"

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
        result = super().parse(string, begin, end)

        # Try to convert the result to an int
        attempt = result.portion

        try:
            value = int(attempt)
        except ValueError:
            return ArgumentError(self.msg_invalid_number.format(
                    number=attempt))
        else:
            if self.min_limit is not None and value < self.min_limit:
                msg = getattr(self, "msg_low_number", self.msg_invalid_number)
                msg = msg.format(number=value)
                return ArgumentError(msg)

            if self.max_limit is not None and value > self.max_limit:
                msg = getattr(self, "msg_high_number", self.msg_invalid_number)
                msg = msg.format(number=value)
                return ArgumentError(msg)

            result.value = value

        return result

    def add_to_namespace(self, result, namespace):
        """Add the parsed number to the namespace."""
        value = result.value
        setattr(namespace, self.dest, value)
