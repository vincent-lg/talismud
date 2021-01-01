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

"""Boolean parsers."""

from scripting.ast import boolean
from scripting.parser.arithmetic import ArExp
from scripting.parser.combinator import Alternate, Concat, Exp, Keyword, Lazy, Symbol
from scripting.parser.parser import Parser

BOOL_CONNECTORS = [
        # Ordered symbols (first hold greater precedence)
        ("and", boolean.AndBoolExp),
        ("or", boolean.OrBoolExp),
]

BOOL_OPERATORS = [
        # Ordered symbols (first hold greater precedence)
        "<",
        "<=",
        ">",
        ">=",
        "==",
        "!=",
]

class BoolConnector(Exp):

    """A conditional connector."""

    def __init__(self, parser, sep, ast):
        self.ast = ast
        self.parser = parser
        self.separator = Keyword(sep)

    def join(self, left, right):
        """Join the two sides of a boolean connector."""
        return self.ast(left, right)


class BoolExp(Parser):

    """Parser for a boolean expression."""

    def __init__(self):
        op, ast = BOOL_CONNECTORS[0]
        self.parser = BoolConnector(BoolExpTerm(), op, ast)
        for op, ast in BOOL_CONNECTORS[1:]:
            self.parser = BoolConnector(self.parser, op, ast)

    async def process(self, tokens):
        """Process the given tokens."""
        return await self.parser.process(tokens)

    def repr(self, seen=None):
        """Return the parser's representation as a string."""
        return self.parser.repr(seen=seen)


class BoolExpTerm(Alternate):

    """
    Basic pieces of a conditional expression.

    A condition statement can be composed of either:
        A not expression (not found).
        A relation (a = b)
        A group ((a != b))

    """

    def __init__(self):
        super().__init__(BoolExpNot(), BoolExpRelop(), BoolExpGroup())


class BoolExpNot(Concat):

    """A not condition."""

    def __init__(self):
        super().__init__(Keyword("not"), Lazy(BoolExpTerm))

    async def process(self, tokens):
        """Process the given tokens."""
        parsed = await super().process(tokens)
        return boolean.NotBoolExp(parsed[1])


class BoolBinOp(Exp):

    """A boolean operation."""

    def __init__(self, parser, sep):
        self.parser = parser
        self.separator = Symbol(sep)
        self.sep = sep

    def join(self, left, right):
        """Join the two sides of an arithmetic operator."""
        return boolean.RelopBoolExp(self.sep, left, right)


class BoolExpRelop(Parser):

    """Parser for a boolean expression."""

    def __init__(self):
        op = BOOL_OPERATORS[0]
        self.parser = BoolBinOp(ArExp(), op)
        for op in BOOL_OPERATORS[1:]:
            self.parser = BoolBinOp(self.parser, op)

    async def process(self, tokens):
        """Process the given tokens."""
        return await self.parser.process(tokens)

    def repr(self, seen=None):
        """Return the parser's representation as a string."""
        return self.parser.repr(seen=seen)


class BoolExpGroup(Concat):

    """A boolean group with simple parenthesis."""

    def __init__(self):
        super().__init__(Symbol('('), Lazy(BoolExp), Symbol(')'))

    async def process(self, tokens):
        """Process the given tokens."""
        parsed = await super().process(tokens)
        return parsed[0][1]
