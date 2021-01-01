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

"""Statement parser, including list of statements."""

from scripting.ast.statement import (
        AssignmentStatement, CompoundStatement, IfStatement, WhileStatement)
from scripting.parser.arithmetic import ArExp
from scripting.parser.boolean import BoolExp
from scripting.parser.combinator import (
        Alternate, Concat, Exp, Keyword, Lazy, Opt, Phrase, Rep, Symbol
)
from scripting.parser.function import FuncCall
from scripting.parser.parser import Parser
from scripting.parser.single import Identifier, Newline

class Program(Phrase):

    """An entire program made of statements."""

    def __init__(self):
        self.parser = Rep(Newline()) + StmtList() + Opt(Newline())

    async def process(self, tokens):
        """Process the tokens."""
        parsed = await self.parser.process(tokens)
        return parsed[0][1]

    def repr(self, seen=None):
        """Return the parser's representation as a string."""
        return self.parser.repr(seen=seen)


class StmtList(Exp):

    """
    Statement list, one or more statements.

    Each statement must be separated by one or more newlines.

    """

    def __init__(self):
        self.parser = Stmt()
        self.separator = Newline()

    def join(self, left, right):
        """Join two separate parts into a single expression (generally AST)."""
        return CompoundStatement(left, right)


class Stmt(Alternate):

    """
    Parser for a single statement.

    A statement can be:
        Assignment: AssignStmt
        If: IfStmt
        While: WhileStmt

    """

    def __init__(self):
        super().__init__(FuncCall(), AssignStmt(), IfStmt(), WhileStmt())


class AssignStmt(Concat):

    """
    Assignment statement, to create or replace a variable.

    Composed of:
        <identifier> = <expression>

    Returns:
        statement (AssignmentStatement): if valid.

    """

    def __init__(self):
        super().__init__(Identifier(), Symbol('='), ArExp())

    async def process(self, tokens):
        """Process the given tokens."""
        parsed = await super().process(tokens)
        var, _, exp = parsed
        return AssignmentStatement(var.name, exp)


class IfStmt(Concat):

    """
    If statement, to wrap an if... block.

    Composed of:
        if <BoolExp>: <NewLine>
          <StmtList>
        [else: <NewLine>
          <StmtList>
        ]
        <NewLine>
        end

    Returns:
        statement (IfStatement) if valid.

    """

    def __init__(self):
        super().__init__(Keyword('if'), BoolExp(), Symbol(':'), Newline(),
                Lazy(StmtList), Opt(Newline() + Keyword('else') +
                Symbol(':') + Newline() + Lazy(StmtList)), Newline(),
                Keyword('end'))

    async def process(self, tokens):
        """Process the tokens."""
        parsed = await super().process(tokens)
        _, condition, _, _, true_stmt, false_parsed, _, _ = parsed
        if false_parsed:
            (_, false_stmt) = false_parsed
        else:
            false_stmt = None

        return IfStatement(condition, true_stmt, false_stmt)


class WhileStmt(Concat):

    """
    While statement.

    Composed of:
        while <BoolExp>:
          <StmpList>
        <Newline>
        end

    Returns:
        statement (WhileStatement): if valid.

    """

    def __init__(self):
        super().__init__(Keyword('while'), BoolExp(), Symbol('-'),
                Newline(), Lazy(StmtList), Newline(), Keyword('end'))

    async def process(self, tokens):
        """Process the given tokens."""
        parsed = await super().process(tokens)
        _, condition, _, _, body, _, _ = parsed
        return WhileStatement(condition, body)
