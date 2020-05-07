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
