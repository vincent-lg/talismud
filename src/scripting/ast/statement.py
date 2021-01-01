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

"""Abstract Syntax Tree for statements."""

from scripting.ast.abc import BaseAST

class AssignmentStatement(BaseAST):

    """Assignment statement, to create or change a variable value."""

    def __init__(self, name, exp):
        self.name = name
        self.exp = exp

    def __repr__(self):
        return f"AssignStatement({self.name} = {self.exp})"

    async def check_types(self, checker):
        """
        Check the types of this AST element.

        Check that this AST uses the right types.  Variable types
        are inferred.  Returns the expected type, or types
        (in a tuple) of this AST, if appropriate.

        Args:
            checker (Typechecker): the type checker.

        Returns:
            type (type, tuple or None): the relevant types of this AST.

        """
        exp_type = await self.exp.check_types(checker)
        checker.set_variable_type(self.name, exp_type)

    async def compute(self, script):
        """
        Add the assembly expressions necessary to compute this AST element.

        Assembly expressions are simple and specialized pieces of
        a script.  They perform one thing and cannot be divided
        into other, smaller expressions.  A script is composed
        of a list of assembly expressions, called an assembly chain.
        It is common for an AST element to create several assembly
        expressions in this chain to represent what to do to evaluate
        this AST element.

        Args:
            script (script.Script): the script object.

        """
        await self.exp.compute(script)
        script.add_expression("STORE", self.name)


class CompoundStatement(BaseAST):

    """Compound statements, composed of two statements."""

    def __init__(self, first, second):
        self.first = first
        self.second = second

    def __repr__(self):
        return f"CompoundStatement({self.first}, {self.second})"

    async def check_types(self, checker):
        """
        Check the types of this AST element.

        Check that this AST uses the right types.  Variable types
        are inferred.  Returns the expected type, or types
        (in a tuple) of this AST, if appropriate.

        Args:
            checker (Typechecker): the type checker.

        Returns:
            type (type, tuple or None): the relevant types of this AST.

        """
        await self.first.check_types(checker)
        await self.second.check_types(checker)

    async def compute(self, script):
        """
        Add the assembly expressions necessary to compute this AST element.

        Assembly expressions are simple and specialized pieces of
        a script.  They perform one thing and cannot be divided
        into other, smaller expressions.  A script is composed
        of a list of assembly expressions, called an assembly chain.
        It is common for an AST element to create several assembly
        expressions in this chain to represent what to do to evaluate
        this AST element.

        Args:
            script (script.Script): the script object.

        """
        await self.first.compute(script)
        await self.second.compute(script)


class IfStatement(BaseAST):

    """If statement."""

    def __init__(self, condition, true_stmt, false_stmt):
        self.condition = condition
        self.true_stmt = true_stmt
        self.false_stmt = false_stmt

    def __repr__(self):
        return f"IfStatement({self.condition}, {self.true_stmt}, {self.false_stmt})"

    async def check_types(self, checker):
        """
        Check the types of this AST element.

        Check that this AST uses the right types.  Variable types
        are inferred.  Returns the expected type, or types
        (in a tuple) of this AST, if appropriate.

        Args:
            checker (Typechecker): the type checker.

        Returns:
            type (type, tuple or None): the relevant types of this AST.

        """
        await self.condition.check_types(checker)
        await self.true_stmt.check_types(checker)
        if self.false_stmt is not None:
            await self.false_stmt.check_types(checker)

    async def compute(self, script):
        """
        Add the assembly expressions necessary to compute this AST element.

        Assembly expressions are simple and specialized pieces of
        a script.  They perform one thing and cannot be divided
        into other, smaller expressions.  A script is composed
        of a list of assembly expressions, called an assembly chain.
        It is common for an AST element to create several assembly
        expressions in this chain to represent what to do to evaluate
        this AST element.

        Args:
            script (script.Script): the script object.

        """
        await self.condition.compute(script)
        after_condition = script.add_expression("IFFALSE", None)
        await self.true_stmt.compute(script)

        if self.false_stmt:
            end_true = script.add_expression("GOTO", None)
            false_line = script.next_line
            script.update_expression(after_condition, "IFFALSE", false_line)
            await self.false_stmt.compute(script)
            script.update_expression(end_true, "GOTO", script.next_line)
        else:
            script.update_expression(after_condition, "IFFALSE", script.next_line)


class WhileStatement(BaseAST):

    """While statement."""

    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def __repr__(self):
        return f"WhileStatement({self.condition}, {self.body})"

    async def check_types(self, checker):
        """
        Check the types of this AST element.

        Check that this AST uses the right types.  Variable types
        are inferred.  Returns the expected type, or types
        (in a tuple) of this AST, if appropriate.

        Args:
            checker (Typechecker): the type checker.

        Returns:
            type (type, tuple or None): the relevant types of this AST.

        """
        await self.condition.check_types(checker)
        await self.body.check_types(checker)

    async def compute(self, script):
        """
        Add the assembly expressions necessary to compute this AST element.

        Assembly expressions are simple and specialized pieces of
        a script.  They perform one thing and cannot be divided
        into other, smaller expressions.  A script is composed
        of a list of assembly expressions, called an assembly chain.
        It is common for an AST element to create several assembly
        expressions in this chain to represent what to do to evaluate
        this AST element.

        Args:
            script (script.Script): the script object.

        """
        before = script.next_line
        await self.condition.compute(script)
        line = script.add_expression("IFFALSE", None)
        await self.body.compute(script)
        script.add_expression("GOTO", before)
        new_line = script.next_line
        script.update_expression(line, "IFFALSE", new_line)
