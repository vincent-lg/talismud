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

"""Module containing the CharacterStream class."""

from typing import Callable, Optional, Sequence, Union

from scripting.exceptions import ParseError

class CharacterStream:

    """
    Stream of characters.

    A stream of characters behaves like a mix bettween a list and a
    string.  It makes lexying easier by offering some methods, making
    it simple to "eat" characters, find matches and "digest" characters
    if a match is found.

    A character stream can be used like this:

        # Look for a :
        if (name := stream.eat_until(":")):
            # This will only executed if a : was found

        # Alternatively you could try in a with statement.
        with stream:
            name = stream.eat_until(":")
        # stream.restore() will be called if an exception occurs
        # stream.digest() will be called if no exception occurred

    Inside of a token `match` method, a character stream is already
    "entered".  Such a method should either parse correctly or raise a
    `ParseERror` exception.  In the former case, the characters "eaten"
    by the token's `match` method will be "digested", that is to say,
    the stream will move on to the next characters.  If a `ParseError`
    exception is raised, however, the stream is "restored", that is to
    say, the characters the token's `match` method read are given back
    to the stream which will try another token class.

    """

    def __init__(self, characters: str, begin: int = 0):
        self._characters = characters
        self._lineno = 1
        self._pos = self._cursor = begin
        remaining = self._characters.splitlines()
        self._line = remaining[0] if remaining else ""

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if type:
            self.restore()
        else:
            self.digest()

        return isinstance(value, ParseError)

    @property
    def pos(self):
        return self._pos

    @property
    def cursor(self):
        return self._cursor

    @property
    def under_pos(self):
        """Return the character under the position."""
        return self._characters[self._pos]

    @property
    def under_cursor(self):
        """Return the character under the cursor."""
        return self._characters[self._cursor]

    @property
    def next_from_pos(self):
        """Return the characters under and after the position."""
        return self._characters[self._pos:]

    @property
    def next_from_cursor(self):
        """Return the character under and after the cursor."""
        return self._characters[self._cursor:]

    def empty(self, check_cursor: bool = False):
        """
        Return True if the stream is empty.

        If `check_cursor` is set to `True`, check whether the temporary
        cursor has read every character.

        Args:
            check_cursor (bool, optional): check the cursor position?

        """
        pos = self._pos
        if check_cursor:
            pos = self._cursor

        return pos == len(self._characters)

    def digest(self):
        """Digest the characters, moving the position forward."""
        self._pos = self._cursor

    def restore(self):
        """Restore the stream as it were before operations were digested."""
        self._cursor = self._pos

    def eat_one(self) -> str:
        """
        Eat only one character and return it.

        Returns:
            character (str): the first character of the stream.

        Note:
            As with every `eat_*` method, the characters will be
            read from the stream using the cursor's position.  Inside
            of a token's `match` method, either return a formed
            token or raise an exception to force the stream to
            "restore" itself, so that the other token classes can
            have a go and test these same characters.

        """
        if not self.empty(check_cursor=True):
            char = self.under_cursor
            if char == "\n":
                self._lineno += 1
                remaining = self._characters[self._cursor + 1:].splitlines()
                self._line = remaining[0] if remaining else ""

            self._cursor += 1
            return char

        self.parse_error("cannot read one more character")

    def eat_until(self, delimiters: str) -> str:
        """
        Eat until the delimiter is found.

        If no delimiter is found, raise a ParseError exception.  If
        the delimiter is found, return everything between the current
        position of the stream until the delimiter (not including it).

        Args:
            delimiters (str): the delimiters to look for.

        Raises:
            ParseError(lineno, line, message): the delimiter wasn't found
                    in the remaining stream.

        """
        pos = self._cursor
        while not self.empty(check_cursor=True):
            char = self.eat_one()
            if any(char.startswith(delimiter) for delimiter in delimiters):
                self._cursor -= 1
                return self._characters[pos:self._cursor]

        self.parse_error("cannot find delimiters.")

    def eat_if(self, test: Callable):
        """
        Eat one character if the specified test returns True.

        Args:
            test (callable): the test.

        The given callable should accept a character
        as argument and return either True or False.  If True,
        the character is returned.  If False, an empty string is returned.

        If the stream is empty, return an empty string.

        Example:
            stream.eat_if(str.isalpha)

        """
        if self.empty(check_cursor=True):
            return ""

        if test(self._characters[self._cursor]):
            self._cursor += 1
            return self._characters[self._cursor - 1]

        return ""

    def eat_if_starts_with(self, beginning: Union[str, Sequence[str]]) -> str:
        """
        Eat characters if the stream starts with the beginning.

        The beginning can be a simple string or a sequence of strings.

        Args:
            beginning (str or sequence of str): the expected beginning.

        Returns:
            begin (str): return the prefix if found, None otherwise.

        Note:
            If one of the beginnings is found, the cursor is moved past
            it.  As usual, either call `digest()` or `restore()`.

        """
        if isinstance(beginning, str):
            # Wrap it in a list
            beginning = list(beginning)

        for prefix in beginning:
            if self._characters[self._cursor:].startswith(prefix):
                self._cursor += len(prefix)
                return prefix

    def eat_while(self, valid: Optional[str] = "",
            test: Optional[Callable] = None) -> str:
        """
        Keep reading while the stream begins with the specified characters.

        Args:
            valid (str, optional): valid characters at the beginning
                    of the stream.
            test (callable, optional): instead of comparing with valid,
                    call a function with, as argument, the first character
                    of the stream.  If it returns `True`, go on.  If it
                    returns `False`, stop.

        This method will raise no error even if the stream is empty.

        Example with `test`:
            matched = characters.eat_while(test=str.isalnum)

        Returns:
            beginning (str): the beginning of the stream which matches
                    the valid characters.

        """
        pos = self._cursor
        while not self.empty(check_cursor=True):
            char = self.eat_one()
            if test and not test(char):
                self._cursor -= 1
                break

            if not test and not any(char.startswith(v) for v in valid):
                self._cursor -= 1
                break

        return self._characters[pos:self._cursor]

    def parse_error(self, message: str):
        """Raise a ParseError."""
        raise ParseError(self._lineno, self._line, message)
