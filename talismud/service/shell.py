from code import InteractiveConsole
import sys

class Shell(InteractiveConsole):

    """Slight modification of the interactive console for TalisMUD."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = ""

    def write(self, data):
        """Write stdout/stderr data."""
        self.output += data

    def push(self, code):
        """Push the code."""
        write = sys.stdout.write
        self.output = ""
        sys.stdout.write = self.write
        more = super().push(code)
        sys.stdout.write = write
        return more
