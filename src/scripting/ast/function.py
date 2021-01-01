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

"""Abstract Syntax Tree classes to represent functions."""

from inspect import signature

from scripting.ast.abc import BaseAST

class FunctionCall(BaseAST):

    """AST to represent a funciton call."""

    def __init__(self, name, arguments):
        self.name = name
        self.arguments = tuple(arguments) if arguments else ()

    def __repr__(self):
        args = ", ".join([repr(argument) for argument in self.arguments])
        return f"FunctionCall({self.name}({args}))"

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
        try:
            function = checker.get_variable_type(self.name)
        except KeyError:
            self.raise_type_error(f"The function {self.name!r} can't be found")

        # Inspect the function argument
        sig = signature(function)

        # Check the argument's annotations
        parameters = {}
        for i, (arg, parameter) in enumerate(
                zip(self.arguments, sig.parameters.values())):
            arg_type = await arg.check_types(checker)
            self.check_issubclass(arg_type, parameter.annotation,
                    f"function {self.name!r}, argument {i} "
                    f"({parameter.name}): expected {{expected_types}}, "
                    f"but got {{value_type}}"
            )
            parameters[parameter.name] = arg_type

        # Check the other parameters
        for i, parameter in enumerate(sig.parameters.values()):
            if parameter.name in parameters:
                continue

            if parameter.default is parameter.empty:
                self.raise_type_error(
                    f"function {self.name!r}, argument {i} "
                    f"({parameter.name}): no value has been set for "
                    f"this mandatory argument"
                )

        # Return the function's return annotation
        return sig.return_annotation

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
        script.add_expression("VALUE", self.name)
        if (arguments := self.arguments):
            for argument in arguments:
                await argument.compute(script)

        script.add_expression("CALL", len(self.arguments))
