from bui import Window

class TalismudWindow(Window):

    """TalisMUD window, powered bh the Blind User Interface."""

    def on_init(self):
        """The window is ready to be displayed."""
        self["status"].value = "TalisMUD isn't running yet."

    async def on_start(self):
        """When clicking on the start button."""
        self["start"].disable()
        self["status"].value = "Starting Talismud, please wait..."
        await self.service.action_start()
        self["start"].disable()
        self["restart"].enable()
        self["stop"].enable()
        self["status"].value = "TalisMUD has been started."

    async def on_restart(self):
        """When clicking on the restart button."""
        self["start"].disable()
        self["restart"].disable()
        self["stop"].disable()
        self["status"].value = "Restarting TalisMUD..."
        await self.service.action_restart()
        self["start"].disable()
        self["restart"].enable()
        self["stop"].enable()
        self["status"].value = "TalisMUD has been started."

    async def on_stop(self):
        """When clicking on the stop button."""
        self["start"].disable()
        self["restart"].disable()
        self["stop"].disable()
        self["status"].value = "Stopping TalisMUD..."
        await self.service.action_stop()
        self["start"].enable()
        self["restart"].enable()
        self["stop"].disable()
        self["status"].value = "TalisMUD has been stopped."
