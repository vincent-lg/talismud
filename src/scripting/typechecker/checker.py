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

class TypeChecker:

    """
    Type checker, to work on a given Abstract Syntax Tree.
    """

    def __init__(self, script):
        self.script = script

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
        await ast.check_types(self)
