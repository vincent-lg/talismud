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

"""Processing combinator.

This combinator is somewhat rare, as sub-parsers often modify
it to extract specific information.  In a functional approach,
however, a process combinator would be used to retrieve specific
data from what has been parsed and shed some of it, as not all
data is needed.

This module is mostly kept for compatibility, and recogniziton
of others' works.

"""

from scripting.exceptions import ParseError
from scripting.parser.parser import Parser

class Process(Parser):

    """Combinator to process a sub-parser."""

    def __init__(self, parser, function):
        self.parser = parser
        self.function = function

    async def process(self, tokens):
        """Let the parser try to process the following token."""
        result = await self.parser.process(tokens)
        return self.function(result)

    def repr(self, seen=None):
        """Return the parser's representation as a string."""
        seen = seen or []
        seen.append(self)
        return f"Process({self.parser.repr(seen=seen)} WITH {self.function})"
