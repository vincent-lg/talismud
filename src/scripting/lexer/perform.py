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

"""Module containing the performing operations of the lexer."""

from scripting.exceptions import ParseError
from scripting.lexer.stream import CharacterStream
from scripting.lexer.abc import TOKEN_CLASSES

def create_tokens(characters: str) -> str:
    """
    Create tokens from a string source code.

    Args:
        characters (str): the characters to read.

    Raises:
        ParseError: an error occurred while reading the tokens.
        NeedMore: the script is not complete, ask for more.

    Returns:
        tokens (list of Token objects): the read tokens.

    """
    stream = CharacterStream(characters)
    tokens = []
    while not stream.empty():
        token = None
        for token_class in TOKEN_CLASSES.values():
            tag = token_class.tag
            lineno = stream._lineno
            line = stream._line
            with stream:
                token = token_class.match(stream)
            if token:
                token.next_pos = stream.pos
                if tag:
                    tokens.append(token)
                    token.lineno = lineno
                    token.line = line
                break
        if not token:
            lineno = stream._lineno
            line = stream._line
            char = stream.eat_one()
            raise ParseError(lineno, line,
                    f"Unexpected character: {char!r}")

    return tokens
