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

"""New email context, displayed when one wishes to create an email address."""

from context.base import BaseContext
from data.account import Account
import settings

class Email(BaseContext):

    """
    Context to set the account email address.

    Input:
        <valid>: move to account.complete.
        <invalid>: invalid email address, gives reason and stays here.
        /: slash, go back to connection.create_password.

    """

    text = """
        Finally, please enter an email address.  This email address
        will ONLY be available to administrators who might need to
        reach you in case of a problem.  This will also help you reset
        your password in case you forgot it.  Additionally, if the game
        has a NewsLetter system or want to share notifications, you can
        receive emails unless you toggle these options off.

        But if you really, really don't want to share your email address,
        just press RETURN.

        Your email address:
    """

    async def input(self, email):
        """The user entered something."""
        # Very basic test to try and filter invalid email adresses
        email = email.strip()
        if email and "@" not in email:
            await self.msg(f"Well!  It sounds like {email!r} isn't a valid email address.  Please try again!")
            return

        account = Account.get(email=email)
        if account:
            await self.msg(
                    f"Sorry, {email!r} is already in use.  Please "
                    "choose another email address.")
            return

        self.session.storage["email"] = email
        await self.msg(
            f"Thank you!  Your email address, {email}, "
            "was successfully registered."
        )
        await self.move("account.complete")
