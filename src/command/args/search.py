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

"""Search argument."""

from typing import Optional, Union

from command.args.base import ArgSpace, Argument, ArgumentError, Result

class Search(Argument):

    """Search class for argument."""

    name = "search"
    space = ArgSpace.UNKNOWN
    in_namespace = True
    _search = None

    def __init__(self, dest, optional=False, default=None):
        super().__init__(dest, optional=optional, default=default)
        self.search_in = None
        self.only_one = True
        self.msg_cannot_find = "'{search}' cannot be found."
        self.msg_mandatory = "You should specify a name to search."

    def __repr__(self):
        return "<Search arg>"

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
        search = type(self)._search
        if search is None:
            from data.search import search
            type(self)._search = search

        end = len(string) if end is None else end
        attempt = string[begin:end]

        # Return an error if the argument is mandatory.
        if not attempt.strip():
            if not self.optional:
                return ArgumentError(self.msg_mandatory)

        # Try searching for the result with this name
        search_in = self.search_in
        if callable(search_in):
            search_in = search_in(character)
        found = None
        if attempt.strip():
            found = search(attempt, limit_to=search_in)

        if not found:
            if attempt.strip():
                return ArgumentError(self.msg_cannot_find.format(
                        search=attempt))

        if self.only_one and found:
            found = found[0] # Ignore the others

        result = Result(begin, end, string)
        result.value = found

        return result

    def add_to_namespace(self, result, namespace):
        """Add the parsed number to the namespace."""
        value = result.value
        setattr(namespace, self.dest, value)
