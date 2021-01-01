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

"""Module containing the TokenStream class."""

from typing import Callable, Optional, Sequence, Union

from scripting.exceptions import ParseError, NoMoreToken
from scripting.lexer.abc import Token

class TokenStream:

    """
    Stream of tokens, usually produced by the lexer.
    """

    def __init__(self, tokens: Sequence[Token], begin: int = 0):
        if not isinstance(tokens, list):
            tokens = list(tokens)
        self._tokens = tokens
        self._pos = self._cursor = begin

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if type:
            self.restore()
        else:
            self.digest()

        return False

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        self._pos = pos

    @property
    def cursor(self):
        return self._cursor

    @cursor.setter
    def cursor(self, cursor):
        self._cursor = cursor

    @property
    def next(self):
        try:
            return self._tokens[self._cursor]
        except IndexError:
            raise NoMoreToken

    def empty(self, check_cursor=False):
        """Return True if the stream is empty."""
        pos = self._cursor if check_cursor else self._pos
        return pos == len(self._tokens)

    def check_empty(self, check_cursor=False):
        """If the stream is empty, raise an exception."""
        if self.empty(check_cursor=check_cursor):
            raise NoMoreToken

    def digest(self):
        """Digest the tokens, moving the position forward."""
        self._pos = self._cursor

    def restore(self):
        """Restore the stream as it were before operations were digested."""
        self._cursor = self._pos

    def eat(self) -> Token:
        """
        Eat one token and return it.

        Returns:
            token (Token): the first token in the stream.

        Note:
            `next` seems to return the same information.  However,
            the `eat` method advances the cursor.  Therefore, the
            token is considered valid unless the token stream is restored.

        """
        if not self.empty():
            token = self._tokens[self._cursor]
            self._cursor += 1
            return token

        self.parse_error("cannot read one more token")

    def parse_error(self, message: str):
        """Raise a ParseError."""
        token = None
        cursor = self._cursor
        while token is None:
            try:
                token = self._tokens[cursor]
            except IndexError:
                cursor -= 1

        lineno = token.lineno
        line = token.line
        raise ParseError(lineno, line, message)
