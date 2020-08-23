# Technical details of scripting in TalisMUD

This document only focuses on the technical aspect of scripting in TalisMUD, how it is implemented in code.  You probably don't need to read through it, except if you are interested in a way to approach the code of the scripting for your own project, or out of mere curiosity.

## Main components, main players

The scripting in TalismUD is handled through a small but thorough interpreter and compiler.  It could be compared to a small programming language in itself.  Although it tries to align with Python syntax, it remains distinct.

The approach to parse and interpret the scripting language is defined in the 'scripting' package.  The main entry point is the `Script` class, defined in 'scripting/script.py'.  Here is a summary of each part before we dive in:

* The first step is to convert a string, containing code, into a list of tokens.  This is done through the [lexer](./lexer.md), defined in the 'scripting.lexer' package.  The [lexer](./lexer.md) itself is pretty light and self-contained.  It browses the string we gave to it and creates tokens or signals errors.  In practice, a line like this:

  `sum = 2 + 4`

  ... would be described in the [lexer](./lexer.md) with 5 tokens: the variable name 'sum', the equal sign (symbol), the integer 2, the plus sign (symbol) and the integer 4.  No parsing is done at this point, the [lexer](./lexer.md) just breaks the string in edible morsels the [parser](./parser.md) will then work with.

* The [parser](./parser.md) is then called.  It is defined in the 'scripting.parser' package.  We feed it the list of tokens, if properly generated.  The [parser](./parser.md) has a more important role: it needs to build a syntax tree.  A syntax tree is a representation of the code, in a hierarchy.  The [parser](./parser.md) decides what is valid and what is not in a token.  For instance, the [parser](./parser.md) will reject an invalid syntax, like '4 33', while the [lexer](./lexer.md) will create two tokens with no difficulty.  The tree constructed by the [parser](./parser.md) is closely tied to the language, removing parts that are not necessary to the language itself, like comments.  Following the same example of:

  `sum = 2 + 4`

  ... and the generated tokens `[ID('sum'), SYMBOL(=), INT(2), SYMBOL(+), INT(4)]`, the [parser](./parser.md) will generate an Abstract Syntax Tree (AST) like this:

  ```python
  AssignmentStatement(sum = Add(Int(2), Int(4)))
  ```

  This is somewhat simplified, but it should help in understanding what happens at this point.  Note that the Abstract Syntax Tree (AST) is defined in the 'scripting.ast' package.  This package is almost exclusively used by the [parser](./parser.md).

* When an Abstract Syntax Tree has been generated, the program can check the types of the program itself.  This is not necessary, but this will help in checking early errors before we interpret the code.  This role is claimed by the [type checker](./typechecker.md) defined in the 'scripting.typechcker' package.  Each piece of the Abstract Syntax Tree (AST) will be called to check the type of data they use and generate errors if something doesn't seem consistent, like adding a number to a string for instance.
* Optionally, a [formatter](./formatter.md) can also be called at this point, to display the entered code in a prettier way.  This is completely optional and will only be used by some areas of the scripting.  They always can be disabled.  See the 'scripting.formatter' package for details.
* With a correct Abstract Syntax Tree (AST), the next step is to "compile" it, that is, generate a list of low-level operations.  This task is also handled by the AST itself, but each piece of compiled code is defined in the 'scripting.assembly' package.  Following the same example, if we have the following AST:

  ```python
  AssignmentStatement(sum = Add(Int(2), Int(4)))
  ```

  The generated [assembly](./assembly.md) will look something like this:

  ```
  1 CONST 2
  2 CONST 4
  3 ADD
  4 STORE 'sum'
  ```

  This sounds a bit hard to read and we only have four lines.  But the computer prefers to handle it in this way.  Let's read it line by line:

  1. First we place a constant, a value onto the "stack".  This value is `2` (an integer).
  2. Then we place a second value, `4`, onto the "stack" as well.
  3. `ADD` is an operation.  it will simply remove the two previous values from the "stack" (`2` and `4`), add them up and place the result back in the "stack".  So `ADD` will remove `2` and `4` and place `6`.
  4. `STORE` is used to create or reassign variables.  The variable name is an argument to `STORE` and the value of this variable should be found on the stack.  So this line will create the `sum` entry in the variables, and assign it `6`, the last entry on the stack at this point.

  The notion of stack can seen somewhat foreign.  It's pretty low-level as-is.  If you're interested, you can read the [assembly page](./assembly.md) for more details.  Having the script in assembly makes it longer, but it makes it easier to execute, easier to pause and start again later.

To conclude this presentation, a script starts its life as a string.  From this string, tokens are created by the [lexer](./lexer.md).  An Abstract Syntax Tree (AST) is created from these tokens by the [parser](./parser.md).  Then an [assembly line](./assembly.md) is generated thanks to this Abstract Syntax Tree.  More often then not, this [assembly line](./assembly.md) is saved and will run pretty fast, the tokens or AST will only be kept when a reversal to a string is necessary.  Scripts are cached, as well, so when a script is executed for the first time, it caches its assembly line and will execute it directly if it's called a second time.  Again, this is a good thing for optimization, since the assembly line will run pretty fast in comparison.
