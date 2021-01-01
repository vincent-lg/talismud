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

"""Abstract assembly expression.

All assembly expressions should inherit from the BaseExpression
class defined below.

"""

from abc import ABCMeta, abstractmethod

EXPRESSIONS = {}

class ExpressionMeta(ABCMeta):

    """Metaclass for all expressions."""

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dict)
        if (name := cls.name):
            EXPRESSIONS[name] = cls


class BaseExpression(metaclass=ExpressionMeta):

    """
    Abstract class for assembly expressions.

    Assembly expressions are the smallest piece of scripting language
    to represent execution of a given behavior.  They use a stack
    (a last-in-first-out queue) to push and pop values and peform
    various processes.  It shouldn't be possible (or useful) to break
    an assembly expression into various other expressions.

    An assembly expression can ressemble somewhat of a line given by
    `dis.dis` in Python: an expression has some definite and well-framed
    behavior (pushing a value onto the stack, calling a function,
    jumping ahead, evaluating a condition...).

    """

    name = "" # Upper-case letter names are better

    @classmethod
    @abstractmethod
    async def process(cls, script, stack):
        """
        Process this expression.

        Args:
            script (Script): the script object.
            stack (LifoQueue): the current stack.
            Other arguments might be expected by other expressions.

        """
        pass
