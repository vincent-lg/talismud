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

"""Abstract class for the Abstract Syntax Tree mechanism."""

from abc import ABCMeta, abstractmethod

from scripting.typechecker.exceptions import TypeCheckerException

class BaseAST(metaclass=ABCMeta):

    """
    Base abstract syntax tree object.

    Methods to override in subclasses:
        __init__(): initialize with any arguments.
        __repr__: more pretty display for debugging.
        compute: create assembly expressions to compute this AST.
        check_types: check the AST types.

    """

    @abstractmethod
    def __init__(self):
        pass

    def __repr__(self):
        return type(self).__name__

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    def check_isinstance(self, value, types, error=None):
        """
        Check whether the given value is an instance of the given types.

        Args:
            value (Any): any value to check.
            types (type or tuple): the type(s) to check.
            error (str, optional): the error message.

        Returns:
            expected_type (type): the matching type, if any.

        If the value is not of the proper types, raises an exception.

        The error message can contain format-specific data (between braces)
        that include:
            {expected_types}: the name of the expected types.
            {value_type}: the type of the value.

        """
        return self.check_issubclass(type(value), types, error)

    def check_issubclass(self, value_types, types, error=None):
        """
        Check whether the given value is a subclass of the given types.

        Args:
            value_types (Any): any type to check.
            types (type or tuple): the type(s) to check.
            error (str, optional): the error message.

        Returns:
            expected_type (type): the matching type, if any.

        If the value is not of the proper types, raises an exception.

        The error message can contain format-specific data (between braces)
        that include:
            {expected_types}: the name of the expected types.
            {value_type}: the type of the value.

        """
        if not isinstance(types, tuple):
            types = (types, )
        if not isinstance(value_types, (list, tuple)):
            value_types = (value_types, )

        if error is None:
            error = (
                    "This value should be of type {expected_types}, "
                    "not of {value_type}"
            )

        for value in value_types:
            for expected_type in types:
                if issubclass(value, expected_type):
                    return expected_type

        expected_types = " or ".join([expected.__name__ for expected in types])
        value_type = value.__name__
        formatted = error.format(expected_types=expected_types,
                value_type=value_type)
        self.raise_type_error(formatted)

    def raise_type_error(self, message):
        """
        Raise a TypeChecker exception.

        Args:
            message (str): the exception message.

        """
        raise TypeCheckerException(message)
