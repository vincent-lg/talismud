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

"""Module containing parsers for single data.

Parsers in this file:
    Floating: a float.
    ID: a variable name.
    Int: an integer.
    Newline: the new line separator.
    String: a string.

"""

from scripting.ast import single as ast
from scripting.exceptions import NoMoreToken, NeedMore
from scripting.parser.combinator import Concat, Opt, Rep, Symbol, Tag
from scripting.parser.parser import Parser

class Floating(Tag):

    """Floating point parser, to parse floats."""

    def __init__(self):
        super().__init__(tag="FLOAT")

    def process(self, tokens):
        """Let the parser try to process the following token."""
        return ast.Float(float(super().process(tokens)))


class Identifier(Parser):

    """
    Identifier parser, to parse variable names.

    Building an identifier parser can take an optional keyword
    argument: `signed`, which is set to `False` by default, will add
    an optional minus symbol before the variable name and allow
    to parse negative identifiers.  This is optional, as in some cases
    (see the AssignmentStatement), the variable should remain unsigned.

    """

    def __init__(self, signed=False):
        self.parser = Tag("ID")
        if signed:
            self.parser = Concat(Opt(Symbol('-')), self.parser)
        self.signed = signed

    def process(self, tokens):
        """Let the parser try to process the following token."""
        parsed = self.parser.process(tokens)
        neg = False
        if isinstance(parsed, list):
            value = parsed[1]
            if parsed[0] == '-':
                neg = True
        else:
            value = parsed

        return ast.ID(value, neg=neg)

    def repr(self, seen=None):
        """Return the parser's representation as a string."""
        return self.parser.repr(seen=seen)


class Integer(Tag):

    """Integer parser, to parse integers."""

    def __init__(self):
        super().__init__(tag="INT")

    def process(self, tokens):
        """Let the parser try to process the following token."""
        return ast.Int(int(super().process(tokens)))


class Newline(Parser):

    """Simple parser to match one new line."""

    def __init__(self):
        self.parser = Symbol("\n") + Opt(Rep(Symbol("\n")))

    def process(self, tokens):
        """Process the separator, raising NeedMore if needed."""
        try:
            tokens.next
        except NoMoreToken:
            raise NeedMore from None

        self.parser.process(tokens)

    def repr(self, seen=None):
        """Return the parser's representation as a string."""
        return "newline"


class String(Tag):

    """
    String parser, to parse strings.

    Note that the lexer is doing most of the process at this
    point, the parser is relatively light in comparison.

    """

    def __init__(self):
        super().__init__(tag="STR")

    def process(self, tokens):
        """Let the parser try to process the following token."""
        return ast.String(super().process(tokens))
