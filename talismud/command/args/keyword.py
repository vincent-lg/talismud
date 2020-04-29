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

"""Keyword argument."""

from typing import Optional, Union

from command.args.base import ArgSpace, Argument, ArgumentError, Result

class Keyword(Argument):

    """Keyword class for argument."""

    name = "keyword"
    space = ArgSpace.WORD
    in_namespace = False

    def __init__(self, dest, optional=False, names=None):
        super().__init__(dest, optional=optional)
        if isinstance(names, str):
            names = (names, )
        self.names = names
        self.msg_cannot_find = "Can't find this argument."

    def __repr__(self):
        return f"<Keyword {'/'.join(self.names)}>"

    def parse(self, string: str, begin: int = 0,
            end: Optional[int] = None) -> Union[Result, ArgumentError]:
        """
        Parse the argument.

        Args:
            string (str): the string to parse.
            begin (int): the beginning of the string to parse.
            end (int, optional): the end of the string to parse.

        Returns:
            result (Result or ArgumentError).

        """
        end = end or len(string)
        for name in self.names:
            if string[begin:].startswith(f"{name} "):
                return Result(begin=begin, end=begin + len(name) + 1,
                        string=string)

            pos = string.find(f" {name} ", begin)
            if pos >= 0 and pos < end:
                return Result(begin=begin + pos,
                        end=begin + len(name) + 2 + pos, string=string)

        self.raise_error(self.msg_cannot_find)
