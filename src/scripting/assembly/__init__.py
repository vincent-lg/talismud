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

"""With a well-formed AST, it's time to flatten the tree.

The assembly chain is a comprehensive representation of the AST, a flattened
version with low-level calls.  Due do its form, it can be interrupted
and scheduled to start again later.  It is not optimized for speed
and will not perform faster than if the AST had the entire
responsability of evaluation, but since most of the parsing has
been done already, it will execute more quickly.

See individual modules in this package for individual expressions.

"""

from scripting.assembly.abc import EXPRESSIONS
from scripting.assembly.add import Add
from scripting.assembly.bool_not import Not
from scripting.assembly.call import Call
from scripting.assembly.const import Const
from scripting.assembly.div import Div
from scripting.assembly.eq import Eq
from scripting.assembly.ge import Ge
from scripting.assembly.goto import Goto
from scripting.assembly.gt import Gt
from scripting.assembly.iffalse import IfFalse
from scripting.assembly.iftrue import IfTrue
from scripting.assembly.le import Le
from scripting.assembly.lt import Lt
from scripting.assembly.mul import Mul
from scripting.assembly.ne import Ne
from scripting.assembly.neg import Neg
from scripting.assembly.store import Store
from scripting.assembly.sub import Sub
from scripting.assembly.value import Value
