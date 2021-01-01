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

"""Parsers for the language implementation."""

ALTERNATE = CONCAT = EXP = PROCESS = None

class Parser:

    """Generic parser from which all parsers must inherit."""

    def __repr__(self):
        return self.repr()

    def __add__(self, other):
        global CONCAT
        if CONCAT is None:
            from scripting.parser.combinator import Concat as CONCAT

        return CONCAT(self, other)

    def __mul__(self, other):
        global EXP
        if EXP is None:
            from scripting.parser.combinator import Exp as EXP

        return EXP(self, other)

    def __or__(self, other):
        global ALTERNATE
        if ALTERNATE is None:
            from scripting.parser.combinator import Alternate as ALTERNATE

        return ALTERNATE(self, other)

    def __xor__(self, function):
        global PROCESS
        if PROCESS is None:
            from scripting.parser.combinator import Process as PROCESS

        return PROCESS(self, function)

    # Display methods
    def repr(self, seen=None):
        """Display the given parsers."""
        return type(self).__name__

    def repr_several(self, connector, *parsers, seen=None):
        """Represent several parsers."""
        seen = seen or []
        results = []
        for parser in parsers:
            if parser in seen:
                results.append(f"{type(parser).__name__}(...)")
            else:
                results.append(f"{parser.repr(seen)}")

        return connector.join(results)
