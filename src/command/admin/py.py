import traceback
from command import Command, CommandArgs
from data.base import db

class Py(Command):

    """
    Command to execute Python code.

    Usage:
        py <Python code to execute>

    """

    alias = "python"
    args = CommandArgs()
    args.add_argument("text", dest="code", optional=True)

    async def run(self, code=""):
        """Run the command."""
        if not code:
            context = self.character.context_stack.add_context("admin.python")
            await context.enter()
            return

        # Create the global variables
        vars = {
                "self": self.character,
                "db": db,
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
            await self.msg(traceback.format_exc(), raw=True)
        else:
            await self.msg(str(result), raw=True)

        await self.msg(">>>")
