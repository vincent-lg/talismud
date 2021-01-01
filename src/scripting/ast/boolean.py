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

"""Boolean and condition Abstract Syntax Tree elements."""

from scripting.ast.abc import BaseAST

OP_NAMES = {
        "==": "EQ",
        ">=": "GE",
        ">": "GT",
        "<=": "LE",
        "<": "LT",
        "!=": "NE",
}

class RelopBoolExp(BaseAST):

    """Relational boolean expression."""

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"RelopBexp({self.op}, {self.left}, {self.right})"

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
        left_type = await self.left.check_types(checker)
        right_type = await self.right.check_types(checker)
        self.check_issubclass(left_type, (int, float))
        self.check_issubclass(right_type, (int, float))
        return bool

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
        name = OP_NAMES[self.op]
        await self.left.compute(script)
        to_update = []
        if isinstance(self.left, RelopBoolExp):
            to_update.append(script.add_expression("IFFALSE", None, False))
            await self.left.right.compute(script)

        await self.right.compute(script)
        if isinstance(self.right, RelopBoolExp):
            to_update.append(script.add_expression("IFFALSE", None, False))
            await self.right.right.compute(script)

        script.add_expression(name)
        for line in to_update:
            script.update_expression(line, "IFFALSE", script.next_line, False)


class AndBoolExp(BaseAST):

    """Boolean expression connected by and."""

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"AndBexp({self.left}, {self.right})"

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
        left_type = await self.left.check_types(checker)
        right_type = await self.right.check_types(checker)
        self.check_issubclass(left_type, bool)
        self.check_issubclass(right_type, bool)
        return bool

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
        await self.left.compute(script)
        line = script.add_expression("IFFALSE", None, False)
        await self.right.compute(script)
        new_line = script.next_line
        script.update_expression(line, "IFFALSE", new_line, False)


class OrBoolExp(BaseAST):

    """Boolean expression connected by or."""

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"OrBexp({self.left}, {self.right})"

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
        left_type = await self.left.check_types(checker)
        right_type = await self.right.check_types(checker)
        self.check_issubclass(left_type, bool)
        self.check_issubclass(right_type, bool)
        return bool

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
        await self.left.compute(script)
        line = script.add_expression("IFTRUE", None, False)
        await self.right.compute(script)
        new_line = script.next_line
        script.update_expression(line, "IFTRUE", new_line, False)


class NotBoolExp(BaseAST):

    """Negative boolean expression."""

    def __init__(self, exp):
        self.exp = exp

    def __repr__(self):
        return f"NotBexp({self.exp})"

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
        self.check_issubclass(exp_type, bool)
        return bool

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
        script.add_expression("NOT")
