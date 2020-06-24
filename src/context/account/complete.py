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

"""Ghost context to complete a new account.

This context will attempt to create an account and will then move to
another.  The user has no chance to input.  It's more a "responsible"
context than an active context.

"""

from pony.orm import commit, OrmError

from context.base import BaseContext
from data.account import Account

class Complete(BaseContext):

    """Ghost context to create an account."""

    async def refresh(self):
        """Try to create an account."""
        username = self.session.storage.get("username")
        password = self.session.storage.get("password")
        email = self.session.storage.get("email")

        # Check that all data are filled
        if username is None or Account.get(username=username):
            await self.msg(
                "Hmmm... something went wrong.  What was your username again?"
            )
            await self.move("account.new")
            return

        if password is None:
            await self.msg(
                "Hmmm... something went wrong.  What was your password again?"
            )
            await self.move("account.create_password")
            return

        if email is None or (email and Account.get(email=email)):
            await self.msg(
                "Hmmm... something went wrong.  What was your email again?"
            )
            await self.move("account.email")
            return

        # Attempt to create the account
        try:
            account = Account.create_with_password(username=username,
                    plain_password=password, email=email)
            commit()
        except OrmError:
            await self.msg("Some error occurred.  We'll have to try again.")
            await self.move("account.new")
            return

        self.session.account = account
        await self.msg(f"The account {username!r} was created successfully.")
        await self.move("character.name")
