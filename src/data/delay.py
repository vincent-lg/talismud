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

"""Permanent delay entity."""

from datetime import datetime, timedelta
import pickle
from typing import Callable, Union

from pony.orm import Required

from data.base import db, PicklableEntity
from tools import delay

class Delay(PicklableEntity, db.Entity):

    """
    Delayed action, to be executed after some time.

    A Delay (delayed action) is similar to a callback that will
    be called after some time.  It is stored in the database, so
    that these actions can persist and run even after a game restart.

    This entity defines persistent delays, that is delays that
    are stored in the database.  See `tools.delay` for delays which
    are only stored if need be.

    """

    expire_at = Required(datetime)
    pickled = Required(bytes, default=pickle.dumps(()))

    @classmethod
    def restore(cls):
        """Schedule all recorded delays in the database."""
        now = datetime.utcnow()
        for persistent in cls.select():
            delta = persistent.expire_at - now
            seconds = delta.total_seconds()
            if seconds < 0:
                seconds = 0

            callback, args, kwargs = pickle.loads(persistent.pickled)
            obj = delay.Delay.schedule(seconds, callback, *args, **kwargs)
            obj.persistent = persistent
