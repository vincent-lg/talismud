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

"""Alternative combinator, to mean "something" or "something else"."""

from scripting.exceptions import ParseError, NoMoreToken
from scripting.parser.parser import Parser

class Alternate(Parser):

    """
    Parser to use alternatively two or more parsers.

    In order to produce a result, the first parser is tried.  If
    it fails, the second parser is presented with the same token.
    And so on.  An error is generated if no parser is able to read the
    given token.

    """

    def __init__(self, *parsers):
        self.parsers = parsers

    async def process(self, tokens):
        """Let the parser try to process the following token."""
        cursor = tokens.cursor
        for parser in self.parsers:
            try:
                result = await parser.process(tokens)
            except (ParseError, NoMoreToken):
                tokens.cursor = cursor
            else:
                return result

        expected = " or ".join([repr(parser) for parser in self.parsers])
        tokens.parse_error(f"expected {expected}")

    def repr(self, seen=None):
        """Return the parser's representation as a string."""
        seen = seen or []
        seen.append(self)
        return "(" + self.repr_several(" | ", *self.parsers, seen=seen) + ")"
