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

"""Abstract object representation.

An object representation is meant to be a thin wrapper around
the object used in the scripting.  For instance, the scripting
uses characters, but allowing full access to the character's
attributes and methods is not wise.  Rather, the character
object representation helps to describe what can be accessed on
the character.

"""

from abc import ABCMeta, abstractmethod

REPRESENTATIONS = {}

class RepresentationMeta(ABCMeta):

    """Metaclass for all object representations."""

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dict)
        if cls.represent:
            REPRESENTATIONS[cls.represent] = cls


class BaseRepresentation(metaclass=RepresentationMeta):

    """
    Abstract class for an object representation.
    """

    represent = None # What class to represent? None means top-level

    def __init__(self, script, object):
        self._script = script
        self._object = None

    def _update(self, script, representer):
        """Update this object representation."""
        self.script = script

    def _get(self, key):
        """Get an attribute from this representation."""
        if key.startswith("_"):
            raise KeyError(key)

        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key) from None
