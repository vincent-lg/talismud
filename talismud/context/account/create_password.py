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

"""Create password context, displayed when one wishes to create a new account."""

from context.base import BaseContext
import settings

class CreatePassword(BaseContext):

    """
    Context to create a new password for a new account.

    Input:
        <valid password>: valid password, move to account.confirm_password.
        <invalid password>: invalid password, gives reason and stays here.
        /: slash, go back to account.new.

    """

    text = """
        Now that you have chosen your account username, you should
        choose a password.  Remember that both the username and password
        will protect your characters on the game.  Other players will
        not be able to see your username and will not know your password,
        unless you tell them, which you shouldn't.

        Preferably choose a password which will be hard to guess, not just
        a word from the dictionary.  You can include letters (without
        or with accents), digits, special characters and so on.  Just
        make sure your password isn't too short.

        Your new password:
    """

    async def input(self, password):
        """The user entered something."""
        # Check that the password isn't too short
        if len(password) < settings.MIN_PASSWORD:
            await self.msg(
                f"This password is incorrect.  It should be "
                f"at least {settings.MIN_PASSWORD} characters long.  "
                "Please try again."
            )
            return

        await self.msg("You selected a password. Great!")
        self.session.storage["password"] = password
        await self.move("account.confirm_password")
