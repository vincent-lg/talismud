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

"""Abstract parser, independent of format.

By default, a created blueprint will have a specific parser instance.
This parser will be used to obtain data (as a sequence of dictionaries)
from a specific location on disk.  You can override the parser,
or add a new one, so that new blueprints use a different format
through a different parser.

A parser is responsible for reading and writing data to the file
system, or another storage system, in a specific format.  Read the
parser's abstract class below.  To create a new parser, add
a class (preferably in its own module), inheriting from the
below `AbstractParser` class and edit new blueprints (see
the setting "BLUEPRINT_PARSER" to change the default parser and
use your new one).

"""

from abc import ABCMeta, abstractmethod
from typing import List

from data.blueprints.blueprint import Blueprint

class AbstractParser(metaclass=ABCMeta):

    """
    Abstract parser.

    Inherit from this class to create a concrete parser you
    can use in a blueprint.

    A parser is a class responsible for reading and writing data.
    The data format and the way this data is stored / retrieved is
    parser-dependent.  In other words, a parser has two responsibilities:

      * Reading and writing data in a specific format.
      * Retrieving and storing data using a storage system.

    Usually, parsers use the file system to store data.  Each blueprint
    is stored in a file.  The blueprint format is YAML by default.
    You can, however, create a parser that uses a TCP connection
    to retrieve and store data, and that uses the JSON format to
    read and write blueprints, for instance.

    The default parser can be set in the game settings.  Entries
    with "BLUEPRINT_*" are used to configure the preferred parser.
    The setting "BLUEPRINT_PARSER" should contain the name of the
    module to use.  Extra information can be specified with other
    "BLUEPRINT*..." keys, where the lowercase name of the setting
    will be sent to the parser.  For instance, the YML parser has an
    option which should contain the path leading to the blueprints.
    You can change it in the settings file with the "BLUEPRINT_DIRECTORY"
    setting.  When the parser is created, a keyword argument named
    "directory" will be used to initialize the parser.  With
    different parsers, you could therefore have different options
    and set them in the settings file.

    Methods to override:
        __init__(records, options as keyword arguments)
        retrieve_blueprints(): return a list of blueprints the parser
                can find.
        store_blueprint: store a single blueprint.
        store_blueprints: store all the found blueprints.

    In writing blueprints, it can be useful to set a backup mode.
    This mode can be changed in the settings, under the key
    "BLUEPRINT_BACKUP".  Parsers are responsible for writing in
    a different way when backup is active.  A backup usually means
    the written file/files do not fully override the previous ones,
    so that data can still be retrieved manually by users, if
    an error occurs.  Remember that, like all settings, changing
    "BLUEPRINT_BACKUP" will affect the parser's "backup" attribute
    (lowercase).  In theory, a parser doesn't need to handle the
    backup mode, but it's still advisable to do so.

    """

    @abstractmethod
    def __init__(self, record, **kwargs):
        """
        Create a parser.

        Additional options will be sent depending on the user settings.
        A setting key with the name "BLUEPRINT_PORT" for instance
        will be sent as a keyword argument of "port" to the
        constructor.  It is preferred to handle arguments in a static
        manner, rather than reading them from kwargs (see
        'data.blueprints.parser.yaml' for an example).

        Args:
            records (dict): the dictionary {record.name: record object}
                    of all `BlueprintRecord` objects found in the
                    database.  This entity is used to keep track
                    of changes and to avoid applying blueprints that
                    haven't changed.  How to handle blueprint records
                    is left to the parser.

        """
        pass

    @abstractmethod
    def retrieve_blueprints(self) -> List[Blueprint]:
        """
        Return a list of blueprints the parser can read and build.

        Blueprints are to be read entirely at this point.  A list
        of blueprints is returned.  Remember, retrieving and applying
        are two different things: reading the list of blueprints
        shouldn't apply any of them.

        """
        pass

    @abstractmethod
    def apply(self):
        """
        Apply blueprints selectively.

        This method should check that applying the blueprint is
        expected and can interact with
        `data.blueprints.record.BlueprintRecord`, which
        is a database table used to "remember" what blueprint
        was applied at what time.

        """
        pass

    @abstractmethod
    def store_blueprint(self, blueprint: Blueprint):
        """
        Store the specified blueprint, to disk or similar.

        The blueprint should be "written", in the parser's format,
        and stored in a system where it can be retrieved later,
        like a file.

        Args:
            blueprint (Blueprint): the blueprint to store.

        """
        pass

    @abstractmethod
    def store_blueprints(self):
        """Store all blueprints."""
        pass
