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

"""Blueprint entity."""

from datetime import datetime
from pathlib import Path
from typing import Callable, Union

from logbook import FileHandler, Logger
from pony.orm import Required
from yaml import safe_load_all

from data.base import db, PicklableEntity
from data.blueprints.blueprint import Blueprint as BP
from data.mixins import HasMixins

# Logger
logger = Logger()
file_handler = FileHandler("logs/blueprints.log",
        encoding="utf-8", level="DEBUG", delay=True)
file_handler.format_string = (
        "{record.time:%Y-%m-%d %H:%M:%S.%f%z} [{record.level_name}] "
        "{record.message}"
)
logger.handlers.append(file_handler)

PARENT = Path("blueprints")

class Blueprint(PicklableEntity, db.Entity, metaclass=HasMixins):

    """
    Keep track of the applied blueprints.

    A blueprint is a file in YML format, stored in the blueprints/
    directory.  Each file is applied when the game starts, but the
    file path and their modification date is stored in the database,
    so that they're not applied unless they're modified again.

    """

    modified = Required(datetime)
    path = Required(str)

    @classmethod
    def should_apply(cls, path: Path) -> bool:
        """Should the specified file be applied?

        Args:
            path (pathlib.Path): the file path.

        It should be applied if it is not present in the database,
        or if the modification date is less recent than the one stored.

        Returns:
            should_apply (bool): thould the file be applied?

        """
        relative = path.relative_to(PARENT)
        record = cls.get(path=str(relative))
        if record is None:
            return True

        # Compare modification dates
        last_modified = datetime.fromtimestamp(path.stat().st_mtime)
        return last_modified > record.modified

    @classmethod
    def extract(cls, path: Path):
        """
        Extract the specified path.

        The path is applied whether should_apply is true or not.
        Therefore, you can use this method to override the should_apply
        decision.

        Args:
            path (pathlib.Path): the path to the file.

        """
        relative = path.relative_to(PARENT)
        record = cls.get(path=str(relative))
        if record is None:
            record = cls(path=str(relative),
                    modified=datetime.fromtimestamp(path.stat().st_mtime))
        else:
            record.modified = datetime.fromtimestamp(path.stat().st_mtime)

        # Read the file
        with path.open("r", encoding="utf-8") as file:
            documents = safe_load_all(file.read())
            blue = BP(list(documents))

        return blue

    @classmethod
    def apply_all(cls, if_needed: bool = True):
        """
        Apply all blueprints.

        By default, only needed blueprints (that is, these that
        have been modified) are applied, the others are ignored.
        You can ovverride this by setting `if_needed` to False.

        Args:
            if_needed (bool, optional): only needed blueprints are applied.

        """
        paths = list(PARENT.rglob("*.yml"))
        logger.debug(
            f"{len(paths)} file{'s' if len(paths) > 1 else ''} "
            f"could be applied."
        )
        for path in paths:
            if if_needed and not cls.should_apply(path):
                logger.debug(f"{path} is ignored.")
                continue

            blue = cls.extract(path)
            num_docs = len(blue.documents)
            logger.info(
                f"Preparing to apply {num_docs} "
                f"document{'s' if num_docs > 1 else ''}"
            )

            blue.apply()
            num_docs = blue.applied
            logger.info(
                f"{path}: applied {num_docs} "
                f"document{'s' if num_docs > 1 else ''}"
            )
