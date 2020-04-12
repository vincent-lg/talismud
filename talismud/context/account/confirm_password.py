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

"""Confirm password context, displayed when one wishes to confirm a new password."""

from context.base import BaseContext
import settings

class ConfirmPassword(BaseContext):

    """
    Context to confirm a new password for a new account.

    Input:
        <identical password>: valid password, move to account.email.
        <different passwords>: go back to account.create_password.
        /: slash, go back to account.create_password.

    """

    text = """
        You've chosen your password.  Please retype it now, to make sure
        you entered it correctly.  If you make a mistake don't
        worry, you'll be asked to create a new passord again.

        Confirm your new password:
    """

    async def input(self, password):
        """The user entered something."""
        original = self.session.storage.get("password", "")

        if not original:
            await self.msg(
                "How did you get here?  Something went wrong, sorry, "
                "better to enter a new password."
            )
            await self.move("account.create_password")
            return

        # Check that the passwords aren't different
        if original != password:
            await self.msg(
                "Oops, it seems you didn't enter the same password.  "
                "To be certain, let's go back to the previous step."
            )
            await self.move("account.create_password")
            return

        # That's the correct password
        await self.msg("Thanks for confirming your password.")
        await self.move("account.email")
