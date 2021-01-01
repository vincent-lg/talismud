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

"""Function parsers."""

from scripting.ast.function import FunctionCall
from scripting.parser.combinator import Concat, Exp, Lazy, Opt, Symbol
from scripting.parser.single import Identifier

ArExp = None

class FuncCall(Concat):

    """
    A function call.

    This expression is composed of:
        An optional minus sign.
        An ID name.
        A left parent.
        Optionally a list of arguments, separated by commas.
        A right parent.

    Return:
        ast (FunctionCall): if correct.

    """

    def __init__(self):
        super().__init__(Opt(Symbol('-')) + Identifier() +
                Symbol('(') + Opt(Argument()) + Symbol(')'))

    async def process(self, tokens):
        """Process the function call."""
        result = await super().process(tokens)
        (((((sign, var), _), arguments), _), ) = result
        if arguments and not isinstance(arguments, list):
            arguments = [arguments]

        ast = FunctionCall(var.name, arguments)
        return ast


class Argument(Exp):

    """Expression parser to read function arguments."""

    def __init__(self):
        global ArExp
        if ArExp is None:
            from scripting.parser.arithmetic import ArExp

        self.parser = Lazy(ArExp)
        self.separator = Symbol(",")

    def join(self, left, right):
        """Join the arguments, making a list if possible."""
        if isinstance(left, list):
            left.append(right)
            return left

        return [left, right]
