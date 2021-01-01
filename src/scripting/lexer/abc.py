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

"""Token module, to host the base class for all tokens."""

from typing import Optional

from scripting.lexer.stream import CharacterStream

TOKEN_CLASSES = {}

class MetaToken(type):

    """Metaclass for token types."""

    def __new__(cls, name, bases, dct):
        token_class = super().__new__(cls, name, bases, dct)
        if token_class.name:
            TOKEN_CLASSES[token_class.name] = token_class
        return token_class


class Token(metaclass=MetaToken):

    """
    Base class for a lexical expression.

    The lexer uses a list of possible tokens.  A token
    is an object designed to match a very small portion of a source
    code, like an integer.

    To add a new token class, simply add a module and a class inheriting
    from `Token` in it.  Override the `match` class method.  This
    should return either `None` if the match couldn't be accomplished
    or an object of this class (a usable token).  For instance:

        class Int(Token):

            # Token class to match an integer

            name = "int"
            tag = "INT"

            @classmethod
            def match(cls, characters):
                # characters is a CharacterStream (see lexer/stream.py)
                if (match := characters.eat_whlie("012345679")):
                    return cls(matched)

    Remember to import the module from the `__init__.py` file as well,
    otherwise it won't be used.

    """

    name = None
    tag = None

    def __init__(self, matched):
        self.matched = matched
        self.next_pos = None
        self.lineno = None
        self.col = None
        self.line = None

    @classmethod
    def match(cls, characters: CharacterStream) -> Optional["Token"]:
        """Return a new token object if a match could be performed."""
        return

    def __repr__(self):
        return f"<Token {self.name}: {self.matched!r}>"
