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

"""Wrapper around all the script steps:

1.  A script object begins by being a string and the lexer is used to
    turn that string into a list of tokens.
2.  This list of token is then fed to the parser.  The parser returns
    a valid Abstract Syntax Tree, if it can.
3.  The Abstract Syntax Tree is checked for type errors.  This step
    is optional and can be deactivated.
4.  The Abstract Syntax Tree is turned into an assembly chain.
    This assembly chain consists of small operations.  The script
    can begin executing this chain and then stop for any reason.

Furthermore, other features also are supported:

*   A script can be built sequentially.  If the parser fails with
    a specific error, wanting a new line of input, then the user
    might add other pieces of the script.  This is somewhat close
    from the behavior emulated by `console.InteractiveConsole`, but
    using the scripting language instead of Python.
*   The script can be "beautified" through a formatter, to make it
    "nicer".  This is quite optional.

To see a simple REPL console, look at `repl.py`.

"""

from queue import Empty, LifoQueue
from typing import Any, List, Optional

from scripting.assembly.abc import EXPRESSIONS
from scripting.assembly.exceptions import MoveCursor
from scripting.ast.abc import BaseAST
from scripting.exceptions import NeedMore
from scripting.lexer.abc import Token
from scripting.lexer.perform import create_tokens
from scripting.parser.perform import parse_tokens
from scripting.namespace import BaseNamespace, TopLevel
from scripting.representation.abc import REPRESENTATIONS, BaseRepresentation
from scripting.typechecker.checker import TypeChecker

# Constants
_NOT_SET = object()

class Script:

    """
    Script, containing all information to execute it.

    A script object can handle all steps, from creating tokens to
    generating the assembly chain and executing it.  It also supports
    "slow" execution that can be paused and started later.  A script
    can be pickled in and by itself, although depending on the needs,
    pickling the assembly chain might be enough.

    To start from a string, do not call the constructor, but call the
    `generate_tokens` class method that will return a `Script` object
    if token generation is successful.  Then, you can try to parse
    the tokens, using the `generate_AST` instance method.  Exceptions
    will be propagated, except for the `NeedMore` exception, that is
    raised to ask the user for more data.  If this exception
    is raised, then the `parse_tokens` method will catch it
    and return False.  Otherwise, it will return `True` or raise
    an exception to indicate the problem.  If parsing is successful,
    the Abstract Syntax Tree (AST) will be written in the script as-is.

    If you have an Abstract Syntax Tree already generated, you can
    also create a script with it.  Tokens will not be used, since
    they can't be infered from the AST itself, but the next mandatory
    steps only work on the AST.

    From there you can call `format` to get the script "nice"
    formatting as a string.  With an AST you also can check types,
    which is only triggered through the `check_types` method and
    can be skipped altogether.  Checking types won't be necessary
    unless the program hasn't been checked before.  Checking types
    can slow down execution in a very small way, so that disabling
    the type checker might be necessary for optimisation in
    a production environment.  However, keep in mind, this step
    is not exactly meant to be always down, scripts fresh
    from the user input should be checked to avoid other runtime
    errors.

    Most useful though, you can call `generate_assembly`
    to generate the assembly chain.  This generation is entirely
    based on the Abstract Syntax Tree.  Again, if the assembly
    chain is generated correctly, it will be made available in
    the script object and you can go to the next step.

    Then you can call `execute` to execute the assembly chain.
    This will begin the "slow" execution of the script.  Instructions
    within the script can stop this "slow" execution and the script
    can be restarted later.

    Note:
        the provided `current_assembly` property generates a picklable
        object with the information necessary to retrieve the script
        from the assembly.  Current variables, cursor position,
        the currrent stack and, of course, the assembly chain itself
        will be kept.
        Even though the script "paused" at a given instruction,
        it's important to store the entire assembly chain
        as some operations will ask to "jump back" to previous positions
        in the chain (this is particularly true for loops).

    Class methods:
        generate_tokens(str): generate the toekens from the given string.
        restore(current_assembly): restore from a stored assembly chain.

    Instance methods:
        add_tokens(str): add more tokens.
        generate_AST(): parse the script tokens into an AST.
        generate_assembly(): generate an assembly chain.
        exe3cute(): start execution of the assembly chain.

    Properties:
        current_assembly: the current assembly chain.

    """

    def __init__(self, tokens: Optional[List[Token]] = None,
            ast: Optional[BaseAST] = None, check_types: bool = True):
        from scripting.representation.character import Character
        self.instructions = None
        self.tokens = tokens or []
        self.ast = ast or None
        self.type_checker = TypeChecker(self) if check_types else None
        self.assembly = None

        # Assembly-specific data
        self.top_level = TopLevel(self)
        self.stack = LifoQueue()
        self.cursor = 0

    def add_tokens(self, to_add: str):
        """
        Try to add the tokens that can be created from the string expression.

        These tokens are added to the token list.  If the Abstract Syntax Tree has been set already, calling this method will result in an error.  A `ParseError` exception will be raised if the given expression can't be parsed into one or more valid tokens.

        Args:
            to_add (str): the piece of the script to add.

        Raises:
            ParseError: the added tokens can't be parsed.

        """
        assert self.ast is None, "The AST already exists"
        tokens = create_tokens(to_add)
        if self.instructions is None:
            self.instructions = ""

        self.instructions += to_add
        self.tokens += tokens

    async def generate_AST(self) -> bool:
        """
        Generate the Abstract Syntax Tree from the tokens.

        This method will try to create a correct Abstract Syntax Tree
        from the provided tokens, and will return `True` if parsing
        was successful and the tree is complete, or `False` to indicate
        it should be expanded (tokens should be added).  It will
        raise other exceptions if parsing can't occur and no additional
        token would resolve the situation.

        Returns:
            parsed (bool): whether parsing was successful.

        Raises:
            ParseError: parsing wasn't successful and no additional
                    token should be sent.

        """
        try:
            ast = await parse_tokens(self.tokens)
        except NeedMore:
            # That's a script, but it's not finished yet, so allow a new line
            self.tokens += create_tokens("\n")
            return False

        self.ast = ast
        return True

    async def check_types(self):
        """
        Check types, through the type checker.

        This step is not mandatory.  If you are positive the program
        you send contains only correct types, then feel free to skip
        this step altogether.  An exception will be raised
        if an incorrect type is used in the program.  Variable
        types are infered from their initial value.  Shadowing
        is allowed (meaning a variable can change type at
        runtime).  Function arguments with or without value
        and their return type is checked, as well as
        operators.

        """
        assert self.type_checker, "no type checker has been set"
        assert self.ast, "the AST hasn't been set yet"
        await self.type_checker.check(self.ast)

    async def generate_assembly(self):
        """
        Generate the assembly chain, using the Abstract Syntax Tree.

        The assembly chain is generated using the script's current
        Abstract Syntax Tree (`ast` attribute).  This attribute must
        exist.  The `generate_AST` method should have been called
        previously.

        If the assembly chain can be generated, it will be written
        in the script's `assembly` attribute.

        """
        assert self.ast, "the Abstract Syntax Tree doesn't exist"
        self.assembly = []
        await self.ast.compute(self)

    def format_assembly(self, individual_lines: bool = False):
        """
        Display the current assembly chain.

        Args:
            individual_lines (bool, optional): display each operation
                    on a single line.

        """
        res = "Script"
        if self.cursor == 0:
            res = f"{res}, ready to flow"
        else:
            res = f"{res}, resuming at expression {self.cursor}"

        expressions = []
        lines = []
        for i, (expression, args) in enumerate(self.assembly):
            if individual_lines or i % 5 == 0:
                size = 0 if individual_lines else 14
                line = " ".join([exp.ljust(size) for exp in expressions])
                lines.append(line)
                expressions = []

            line = str(i).rjust(len(str(len(self.assembly) - 1)))
            if self.cursor == i:
                line += "*"
            line += f" {expression.name}"
            arguments = " ".join([repr(arg) for arg in args])
            size = 65 if individual_lines else 13
            if len(line) + len(arguments) > size:
                line += f"...{len(args)}"
            else:
                line += f" {arguments}"
            expressions.append(line)

        size = 0 if individual_lines else 14
        line = " ".join([exp.ljust(size) for exp in expressions])
        lines.append(line)
        return res + "\n" + "\n".join(lines)

    def set_default_variables(self, **kwargs):
        """
        Set the script's default variables.

        This allows to set variables prior to executing the script.
        Variables are converted to their object representation
        if necessary.

        Args:
            Any keyword argument would be a variable name and value.

        """
        for key, value in kwargs.items():
            self.set_variable_or_attribute(key, value)

    @property
    def next_line(self):
        """Return the assembly's next available line."""
        return len(self.assembly)

    def empty_stack(self):
        """
        Empty and return the values in the stack.

        Tries to return it as a singular value, that is, if there's
        only one value in the stack.  Otherwise, returns a tuple of values.

        Note:
            This method, as its name suggests, will empty the stack.
            DO NOT use it if the script is paused and to be started
            again later.  The stack should remain consistent between
            calls of the script.

        """
        values = []
        while True:
            try:
                value = self.stack.get(block=False)
            except Empty:
                break
            else:
                values.append(value)

        if len(values) < 2:
            return values[0] if values else None

        return tuple(values)

    def add_expression(self, expression: str, *args) -> int:
        """
        Add an assembly expression at the end of the script.

        This method should only be used inside of AST elements that
        'compute' to the assembly chain.

        Args:
            expression (str): the expression name.
            Additional arguments are the expression arguments.

        Returns:
            line (int): the line on which the expression was added.

        Raises:
            KeyError: the expression couldn't be found.

        """
        exp_class = EXPRESSIONS[expression]
        self.assembly.append((exp_class, args))
        return len(self.assembly) - 1

    def update_expression(self, line: int, expression: str, *args) -> int:
        """
        Update an existing expression at the given line.

        This method should only be used inside of AST elements that
        'compute' to the assembly chain.

        Args:
            line (int): tthe line number to edit.
            expression (str): the expression name.
            Additional arguments are the expression arguments.

        Returns:
            line (int): the line on which the expression was updated.

        Raises:
            KeyError: the expression couldn't be found.
            IndexError: the specified index is incorrect.

        """
        exp_class = EXPRESSIONS[expression]
        self.assembly[line] = (exp_class, args)
        return line

    async def execute(self):
        """
        Start the slow execution of this script.

        This method should be called when the assembly chain
        (attribute `assembly`) is provided.  Execution will start
        and only stop if the `StopScript` exception is raised.
        In this case, the program can be "restarted" later.
        If the game has to restart in the meantime, the program
        can be pickled.  It's advisable to store `current_assembly`
        and restore the program from it (see `restore`).

        """
        stack = self.stack
        while self.cursor < len(self.assembly):
            exp_class, args = self.assembly[self.cursor]
            try:
                await exp_class.process(self, stack, *args)
            except MoveCursor as exc:
                self.cursor = exc.cursor
            else:
                self.cursor += 1

    def clear(self):
        """
        Clear the script, remonving tokens, AST and assembly.

        This doesn't remove variables (and data in the type checker, if any).

        """
        self.tokens = []
        self.ast = None
        self.assembly = []
        self.cursor = 0

    def reset(self):
        """
        Reset the script to be ready for execution.

        This will remove variables and reset the cursor at the default
        0 position, without affecting the tokens, AST and assembly.

        """
        self.cursor = 0
        self.top_level = TopLevel(self)
        self.stack = LifoQueue()

    def get_variable_or_attribute(self, name: str):
        """
        Return the attribute or variable with this name.

        Args:
            name (str): a name, with the usual notation (a.b.c).

        Returns:
            value (Any): the value, of any type, if successful.

        Raises:
            KeyError: the name cannot be found.

        """
        split = name.split(".")
        value = self.top_level.attributes[split[0]]
        for sub_name in split[1:]:
            if isinstance(value, BaseNamespace):
                value = value.attributes[sub_name]
            elif isinstance(value, BaseRepresentation):
                value = value._get(sub_name)
            else:
                value = getattr(value, sub_name)

        return value

    def set_variable_or_attribute(self, name: str, value: Any):
        """
        Change the attribute or variable's value.

        Args:
            name (str): a name, with the usual notation (a.b.c).

        Raises:
            KeyError: the name cannot be found.

        """
        split = name.split(".")
        if len(split) > 1:
            obj = self.get_variable_or_attribute(name.rsplit(".", 1)[0])
            sub_name = split[-1]
        else:
            obj = self.top_level
            sub_name = name

        try:
            old_value = self.get_variable_or_attribute(name)
        except KeyError:
            old_value = _NOT_SET

        # Wrap value in an object representation if needed
        representation = REPRESENTATIONS.get(type(value))
        if representation:
            if old_value is _NOT_SET:
                value = representation(self, value)
            else:
                old_value._update(self, value)
                return

        if isinstance(obj, BaseNamespace):
            obj.attributes[sub_name] = value
        elif isinstance(obj, BaseRepresentation):
            obj._set(sub_name, value)
        else:
            setattr(obj, sub_name, value)

    def restore_top_level(self, top_level: TopLevel):
        """
        Restore the top-level namespace, from another script.

        This is mostly used for debugging purposes, where
        several script objects are created but variables
        should be carried from one to the other.

        Args:
            top_level (TopLevel): the top-level namespace.

        """
        self.top_level = top_level
        queue = LifoQueue()
        queue.put(top_level, block=False)

        while not queue.empty():
            namespace = queue.get(block=False)
            namespace.script = self
            for value in namespace.attributes.values():
                if isinstance(value, BaseNamespace):
                    queue.put(value, block=False)

    @classmethod
    def generate_tokens(cls, instructions: str):
        """
        Return a new script with tokens.

        If successful, return a new Script object with instructions
        turned into valid tokens.

        Args:
            instructions (str): the script's instructions.

        """
        script = cls()
        script.add_tokens(instructions)
        return script
