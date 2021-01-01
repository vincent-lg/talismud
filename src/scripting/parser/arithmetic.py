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

"""Arithmetic parsers."""

from scripting.ast.arithmetic import MulOp, DivOp, AddOp, SubOp
from scripting.parser.combinator import (
        Alternate, Exp, Keyword, Lazy, Opt, Phrase, Symbol)
from scripting.parser.function import FuncCall
from scripting.parser.parser import Parser
from scripting.parser.single import Floating, Identifier, Integer, String

AR_OPERATORS = [
        # Ordered symbols (first hold greater precedence)
        ("*", MulOp),
        ("/", DivOp),
        ("+", AddOp),
        ("-", SubOp),
]

class FullExpression(Phrase):

    """Full expression, a phrase wrapping the arithmetic expression."""

    def __init__(self):
        self.parser = ArExp()


class ArBinOp(Exp):

    """An arithmetic operation."""

    def __init__(self, parser, sep, ast):
        self.ast = ast
        self.parser = parser
        self.separator = Symbol(sep)

    def join(self, left, right):
        """Join the two sides of an arithmetic operator."""
        return self.ast(left, right)


class ArExp(Parser):

    """Parser for an arithmetic expression."""

    def __init__(self):
        op, ast = AR_OPERATORS[0]
        self.parser = ArBinOp(ArExpTerm(), op, ast)
        for op, ast in AR_OPERATORS[1:]:
            self.parser = ArBinOp(self.parser, op, ast)

    async def process(self, tokens):
        """Process the given tokens."""
        return await self.parser.process(tokens)

    def repr(self, seen=None):
        """Return the parser's representation as a string."""
        return self.parser.repr(seen=seen)


class ArExpTerm(Alternate):

    """
    A simple arithmetic element.

    This can be:
        ArExpValue: a function, a variable or a value.
        ArExpGroup: a simple group with parenthesis.

    """

    def __init__(self):
        super().__init__(ArExpValue(), ArExpGroup())


class ArExpGroup(Parser):

    """
    An arithmetic expression group with simple parenthesis.

    Note: this would encompass (3) for instance, but also
    (1 + 2) since the expression between parenthesis
    can be an artihmetic expression.  Therefore, it follows
    that an expression like ((3 + 2) * 5) / 2 will
    be parsed correctly by successive groups.

    """

    def __init__(self):
        self.parser = (
                Opt(Symbol("-")) + Symbol('(') + Lazy(ArExp) + Symbol(')')
        )

    async def process(self, tokens):
        """Try to process the expression."""
        result = await self.parser.process(tokens)
        (((sign, _), p), _) = result
        if sign == '-':
            p.neg = True
        return p

    def repr(self, seen=None):
        """Return the parser's representation as a string."""
        return self.parser.repr(seen=seen)


class ArExpValue(Alternate):

    """
    An arithmetic expression value.

    Composed of either:
        A variable (identifier).
        A value (integer, floating or string).

    """

    def __init__(self):
        super().__init__(FuncCall(), Integer(), Floating(),
                Identifier(signed=True), String())
