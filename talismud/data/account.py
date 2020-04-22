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

"""Account entity.

An account plays the role of an intermediate between a connection
from a player (a session object), and one or more characters.  The
account contains the username, hashed password and email address of
the player.  One or more characters can be gathered in the same account.
Even if you plan to have only one character per account, this separation
is useful (no need to put passwords in characters, after all).

"""

from datetime import datetime
import hashlib
import os
import typing as ty

from pony.orm import Optional, Required, Set

from data.attribute import AttributeHandler
from data.base import db, PicklableEntity
from data.mixins import HasMixins, HasStorage
from data.properties import lazy_property
import settings

class Account(HasStorage, PicklableEntity, db.Entity, metaclass=HasMixins):

    """Account entity, to connect a session to characters."""

    username = Required(str, max_len=64, unique=True)
    hashed_password = Required(bytes)
    email = Optional(str, max_len=320, unique=True, index=True)
    created_on = Required(datetime, default=datetime.utcnow)
    updated_on = Required(datetime, default=datetime.utcnow)
    sessions = Set("Session")
    characters = Set("Character")
    attributes = Set("AccountAttribute")

    @lazy_property
    def db(self):
        return AttributeHandler(self)

    def before_update(self):
        """Change the 'updated_on' datetime."""
        self.updated_on = datetime.utcnow()

    def is_correct_password(self, password: str) -> bool:
        """
        Return whether the given password is correct for this account.

        Args:
            password (str): the plain text password.

        Returns:
            correct (bool): whether this password is correct.

        """
        return self.test_password(self.hashed_password, password)

    @classmethod
    def create_with_password(cls, username: str, plain_password: str,
            email: ty.Optional[str]) -> "Account":
        """
        Create a new account object and hash its plain password.

        Passwords aren't stored in clear in the database.  This method
        will hash the password according to settings and will create and
        return an account object with this hashed password.

        Args:
            username (str): the username.
            plain_password (str): the password (in plain text).
            email (str, optional): the optional email address.

        Returns:
            new_account (Account): the new account with a hashed password.

        """
        password = cls.hash_password(plain_password)
        return cls(username=username, hashed_password=password, email=email)

    @staticmethod
    def hash_password(plain_password: str,
            salt: ty.Optional[bytes] = None) -> bytes:
        """
        Hash the given plain password, return it hashed.

        If the salt is provided, it is used for hhashing.  If not,
        it is randomly generated.

        Args:
            plain_password (str): the plain password.
            salt (bytes, optional): the salt to use to hash the password.

        Args:
            hashed_password (bytes): the hashed passowrd containing
                    the salt and key.

        """
        if salt is None:
            # Generate a random salt
            salt = os.urandom(settings.SALT_SIZE)

        # Hash the password with pbkdf2_hmac
        key = hashlib.pbkdf2_hmac(settings.HASH_ALGORITHM,
                plain_password.encode("utf-8"), salt,
                settings.HASH_ITERATIONS, settings.KEY_SIZE)

        return salt + key

    @staticmethod
    def test_password(hashed_password: bytes, plain_password: str) -> bool:
        """Return whether the hashed and non hashed password match."""
        salt = hashed_password[:settings.SALT_SIZE]
        key = hashed_password[settings.SALT_SIZE:]
        hashed_attempt = Account.hash_password(plain_password, salt)
        return hashed_password == hashed_attempt
