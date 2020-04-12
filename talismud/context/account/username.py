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

"""New account context, displayed when one wishes to create a new account."""

from context.base import BaseContext
from data.account import Account
import settings

class Username(BaseContext):

    """
    Context called when the user wishes to create a new account.

    Input:
        <new username>: valid username, move to account.create_password.
        <invalid>: invalid username, gives reason and stays here.
        /: slash, go back to connection.home.

    """

    text = """
        New user, welcome to TalisMUD!

        You wish to create a new account.  The first step for you is
        to create a username.  This username (and the password you will
        select next) will be needed to access your characters.
        You should choose both a username and password no one can easily
        guess.

        Please enter your username here:
    """

    async def input(self, username):
        """The user entered something."""
        username = username.lower().strip()

        # Check that the name isn't too short
        if len(username) < settings.MIN_USERNAME:
            await self.msg(
                f"The username {username!r} is incorrect.  It should be "
                f"at least {settings.MIN_USERNAME} characters long.  "
                "Please try again."
            )
            return

        # Check that the username isn't a forbidden name
        if username in settings.FORBIDDEN_USERNAMES:
            await self.msg(
                f"The username {username!r} is forbidden.  Please "
                "choose another one."
            )
            return

        # Check that nobody is using this username
        account = Account.get(username=username)
        if account:
            await self.msg(
                f"The username {username!r} already exists.  Please "
                "choose another one."
            )
            return

        await self.msg(f"You selected the username: {username!r}.")
        self.session.storage["username"] = username
        await self.move("account.create_password")
