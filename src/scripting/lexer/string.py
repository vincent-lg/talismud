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

"""String token."""

from textwrap import dedent

from scripting.exceptions import NeedMore, ParseError
from scripting.lexer.abc import Token

SYNTAX = (
        # (Name, begin, end, multiline),
        ("mul_pre", '""|', '|""', True),
        ("mul_ded", '"">', '<""', True),
        ("uni", "'", "'", False),
        ("uni", '"', '"', False),
)

class String(Token):

    """
    Expression to match strings.

    A string can have several syntax:
        "one string without line break"
        'one string without line break'
        "">
            A paragraph
            with line breaks.
            The paragraphes are dedented-ed and line breaks are removed.
        <""
        ""|
            A paragraph
            with line breaks.
            The paragraphes are dedented-ed and line breaks are preserved.
        |""

    """

    name = "string"
    tag = "STR"

    @classmethod
    def match(cls, characters):
        """Return a new expression if a match could be performed."""
        string = ""
        for name, begin, end, multiline in SYNTAX:
            characters.restore()
            if characters.next_from_cursor.startswith(begin):
                for _ in range(len(begin)):
                    characters.eat_one()

                while not characters.next_from_cursor.startswith(end):
                    try:
                        char = characters.eat_one()
                    except ParseError:
                        raise NeedMore from None
                    else:
                        if char == '\n' and not multiline:
                            characters.parse_error(
                                    "multiline strings are not supported "
                                    "with this syntax"
                            )

                        string += char

                # End of the string, eat the delimiters
                for _ in range(len(end)):
                    characters.eat_one()

                # Format according to the syntax
                if name in ("mul_pre", "mul_ded"):
                    string = dedent(string.lstrip("\n").rstrip())

                if name == "mul_ded":
                    # Replace \n with spaces
                    string = ' '.join([line.strip() for line in
                            string.splitlines()])

                # And stop there, no point in trying the other alternatives
                break
        else: # No match was found
            characters.parse_error("this is not a string")

        # At this point we've found a string, return a new expression
        return cls(string)
