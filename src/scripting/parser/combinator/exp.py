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

"""Specialized parser to parse expressions."""

from scripting.exceptions import ParseError, NoMoreToken, NeedMore
from scripting.parser.parser import Parser

class Exp(Parser):

    """
    Specialized parser to parse an expression.

    This type of parser accepts a sub-parser and an operator.  The
    parsing occurs like this: sub-parser, operator, sub-parser,
    operator, sub-parser, operator, ..., sub-parser.

    """

    def __init__(self, parser, separator):
        self.parser = parser
        self.separator = separator

    async def process(self, tokens):
        """Let the parser try to process the following token."""
        result = await self.parser.process(tokens)
        next_parser = self.separator + self.parser

        while True:
            try:
                next_result = await next_parser.process(tokens)
            except (ParseError, NoMoreToken, NeedMore):
                break
            else:
                if next_result[0] and callable(next_result[0]):
                    result = next_result[0](result, next_result[1])
                else:
                    result = self.join(result, next_result[1])

        return result

    def join(self, left, right):
        """Join two separate parts into a single expression (generally AST)."""
        raise NotImplementedError

    def repr(self, seen=None):
        """Return the parser's representation as a string."""
        seen = seen or []
        seen.append(self)
        return "Exp(" + self.repr_several(" AND ", self.parser, self.separator, seen=seen) + ")"
