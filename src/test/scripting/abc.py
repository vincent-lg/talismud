"""Abstract base test."""

import asyncio
from typing import Any, Dict, Optional

from scripting.script import Script
from test.base import BaseTest

class ScriptingTest(BaseTest):

    """Base class for unittests in scripting."""

    def write_script(self, instructions: str,
            variables: Optional[Dict[str, Any]] = None,
            check_types: Optional[bool] = True):
        """
        Write and return a new script with the specified instructions.

        Args:
            instrucitons (str): the instructions to be entered.
            variables (dict, optional): the default variables.
            check_types (bool, optional): whether to run the type
                    checker or not (True by default).

        Note:
            Not running the type checker will make the script run faster,
            but the result might not be consistent, particularly
            in case of errors.  Should error handling be tested,
            the `check_types` argument should always be True.

        Returns:
            script (Script): the new and executed script.

        This method will start a new script with the specified
        instructions, create the tokens, the AST and assembly,
        then execute the script and return it.  Being in a synchronous
        test environment, this method will run asynchronous
        methods in an async loop and pause while these methods process.
        Thus, the process of script execution will not be exactly
        consistent with the way scripts are handled and
        run in the game itself.  On the other hand, this method doesn't
        cache scripts and create a new instance of
        one each time.

        """
        script = Script()
        script.add_tokens(instructions)
        asyncio.run(script.generate_AST())

        if variables:
            script.set_default_variables(**variables)

        if check_types:
            asyncio.run(script.check_types())

        asyncio.run(script.generate_assembly())
        asyncio.run(script.execute())
        return script
