import traceback
from command import Command, CommandArgs

class Py(Command):

    """
    Command to execute Python code.

    Usage:
        py <Python code to execute>

    """

    args = CommandArgs()
    args.add_argument("text", "code")

    async def run(self, args):
        """Run the command."""
        # Create the global variables
        vars = {
                "self": self.character,
        }

        # First try to evaluate it
        try:
            result = eval(args.code, vars)
        except SyntaxError:
            # Now try running in exec mode
            try:
                exec(args.code, vars)
            except Exception:
                await self.msg(traceback.format_exc())
            else:
                await self.msg("Done.")
        except Exception:
            await self.msg(traceback.format_exc())
        else:
            await self.msg(str(result))

