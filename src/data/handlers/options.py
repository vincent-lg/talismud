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

"""Option handler, to work with an inline dictionary.

Contrary to most handlers, the OptionHandler requires a
`binary_options` field, set as a required byte string on the
entity it modifies.

"""

import pickle

from collections.abc import MutableMapping

class OptionHandler(MutableMapping):

    """Option handler, to handle options in a dictionary-like object.

    The option handler is an object which uses a binary representation,
    stored in the entity itself.  It has all the methods one can expect
    from a dictionary and can be used as such.

        >>> session.options["username"] = "someone"
        >>> session.options["username"]
        'someone'
        >>> len(session.options)
        1
        >>> del session.options["username"]
        >>> sesession.options.get("username", "")
        ''
        >>> # ...

    """

    __slots__ = ("__owner", "__binary_field", "__options")

    def __init__(self, owner, binary_field="binary_options"):
        self.__owner = owner
        self.__binary_field = binary_field
        binary = getattr(owner, binary_field)
        self.__options = pickle.loads(binary)

    def __len__(self):
        return len(self.__options)

    def __iter__(self):
        return iter(self.__options)

    def __getitem__(self, key):
        return self.__options[key]

    def __setitem__(self, key, value):
        self.__options[key] = value
        setattr(self.__owner, self.__binary_field, pickle.dumps(
                self.__options))

    def __delitem__(self, key):
        del self.__options[key]
        setattr(self.__owner, self.__binary_field, pickle.dumps(
                self.__options))
