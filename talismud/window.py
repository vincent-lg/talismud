from bui import Window

from service.launcher import MUDOp, MUDStatus

class TalismudWindow(Window):

    """TalisMUD window, powered bh the Blind User Interface."""

    def on_init(self):
        """The window is ready to be displayed."""
        self["status"].value = "Getting MUD status..."
        self.schedule(self.check_status())

    async def check_status(self):
        """Try to report on the MUD status."""
        await self.service.check_status()
        if self.service.status == MUDStatus.ALL_ONLINE:
            self["status"].value = "TalisMUD has been started."
            self["start"].disable()
            self["restart"].enable()
            self["stop"].enable()
        elif self.service.status == MUDStatus.OFFLINE:
            self["status"].value = "TalisMUD is stopped."
            self["start"].enable()
            self["restart"].disable()
            self["stop"].disable()

    async def on_start(self):
        """When clicking on the start button."""
        self["start"].disable()
        self["status"].value = "Starting Talismud, please wait..."
        await self.service.action_start()
        await self.check_status()

        # If an admin is needed
        if MUDOp.NEED_ADMIN in self.service.operations:
            dialog = self.pop_dialog("""
                <dialog title="New admin account">
                  <text x=1 y=2 id=username>Enter your new username:</text>
                  <text x=1 y=3 id=password hidden>Enter your account password:</text>
                  <text x=1 y=4 id=email>Enter your optional account email address:</text>
                  <button x=5 y=2 set_true>OK</button>
                  <button x=5 y=4 set_false>Cancel</button>
                </dialog>
            """)

            if dialog:
                username = dialog["username"].value
                password = dialog["password"].value
                email = dialog["email"].value
                success = await self.service.action_create_admin(username,
                        password, email)

                if success:
                    self.pop_dialog("""
                        <dialog title="Success">
                          <text x=1 y=2 id=message read-only>
                            Your new administrator account was successfully
                            created.
                          </text>
                          <button x=5 y=2 set_true>OK</button>
                        </dialog>
                    """)
                else:
                    self.pop_dialog("""
                        <dialog title="Error">
                          <text x=1 y=2 id=message read-only>
                            The administrator account couldn't be created.
                          </text>
                          <button x=5 y=2 set_true>OK</button>
                        </dialog>
                    """)

    async def on_restart(self):
        """When clicking on the restart button."""
        self["start"].disable()
        self["restart"].disable()
        self["stop"].disable()
        self["status"].value = "Restarting TalisMUD..."
        await self.service.action_restart()
        await self.check_status()

    async def on_stop(self):
        """When clicking on the stop button."""
        self["start"].disable()
        self["restart"].disable()
        self["stop"].disable()
        self["status"].value = "Stopping TalisMUD..."
        await self.service.action_stop()
        await self.check_status()
