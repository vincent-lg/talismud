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

"""Type checker, to check the program's types.

The type checker runs on the Abstract Syntax Tree to check whether the
data types it uses are consistent.  Variables, function parameters,
return values and operations are checked for consistency.
The type checker is optional in itself and one can turn it down
to optimize compilation of a script.  However, this is not really
desirable and might lead to errors.  The types are checked only
when the script (initially string) is turned into an assembly chain,
so the type checker doesn't slow down execution in the least.

"""

from queue import Queue
from typing import Any

from scripting.namespace.abc import BaseNamespace
from scripting.representation.abc import REPRESENTATIONS, BaseRepresentation

# Constants
_NOT_SET = object()

class TypeChecker:

    """
    Type checker, to work on a given Abstract Syntax Tree.
    """

    def __init__(self, script):
        self.script = script
        self.variables = {}

    async def check(self, ast):
        """
        Check the abstract syntax tree's types.

        Args:
            ast (ast.BaseAst): an AST object.

        Raises:
            Subclass of TypeCheckingError to let the user know there's
            an error in the syntax tree.

        Note:
            The AST object is actually left in charge of checking
            itself through the `check_types` method.

        """
        self.update_variables()
        await ast.check_types(self)

    def update_variables(self):
        """Update the type checker's variables with the script variables."""
        top_level = self.script.top_level
        namespaces = Queue()
        namespaces.put((None, top_level))

        while not namespaces.empty():
            name, namespace = namespaces.get()
            for key, value in namespace.attributes.items():
                sub_name = name
                if sub_name is not None:
                    sub_name += "." + key
                else:
                    sub_name = key

                self.set_variable_type(sub_name, value)
                if isinstance(value, BaseNamespace):
                    namespaces.put((sub_name, value))

    def get_variable_type(self, name: str):
        """
        Return the variable type with this name.

        Args:
            name (str): a name, with the usual notation (a.b.c).

        Returns:
            var_type (Any): the variable type.

        Raises:
            KeyError: the name cannot be found.

        """
        split = name.split(".")
        var_type = self.variables[split[0]]
        for sub_name in split[1:]:
            if isinstance(var_type, BaseNamespace):
                var_type = var_type.attributes[sub_name]
            elif isinstance(var_type, BaseRepresentation):
                var_type = var_type._get(sub_name)
            else:
                var_type = getattr(var_type, sub_name)

        return var_type

    def set_variable_type(self, name: str, var_type: Any):
        """
        Change the attribute or variable's type.

        Args:
            name (str): a name, with the usual notation (a.b.c).

        Raises:
            KeyError: the name cannot be found.

        """
        split = name.split(".")
        if len(split) > 1:
            obj = self.get_variable_type(name.rsplit(".", 1)[0])
            sub_name = split[-1]
        else:
            obj = self.variables
            sub_name = name

        try:
            old_type = self.get_variable_type(name)
        except KeyError:
            old_value = _NOT_SET

        # Wrap value in an object representation if needed
        representation = (REPRESENTATIONS.get(var_type) or
                REPRESENTATIONS.get(type(var_type)))
        if representation:
            if old_type is _NOT_SET:
                var_type = representation(self.script, var_type)
            else:
                old_type._update(self.script, var_type)
                return

        if isinstance(obj, BaseNamespace):
            obj.attributes[sub_name] = var_type
        elif isinstance(obj, BaseRepresentation):
            obj._set(sub_name, var_type)
        elif isinstance(obj, dict):
            obj[sub_name] = var_type
        else:
            setattr(obj, sub_name, var_type)
