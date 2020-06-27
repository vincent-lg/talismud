import traceback
from command import Command, CommandArgs

class Py(Command):

    """
    Command to execute Python code.

    Usage:
        py <Python code to execute>

    """

    args = CommandArgs()
    args.add_argument("text", dest="code")

    async def run(self, code):
        """Run the command."""
        # Create the global variables
        vars = {
                "self": self.character,
        }

        # First try to evaluate it
        try:
            result = eval(code, vars)
        except SyntaxError:
            # Now try running in exec mode
            try:
                exec(code, vars)
            except Exception:
                await self.msg(traceback.format_exc())
        except Exception:
            await self.msg(traceback.format_exc())
        else:
            await self.msg(str(result))

        await self.msg(">>>")
