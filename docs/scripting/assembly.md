# Assembly, assembly chain in scripting

A script in TalisMUD will go through several steps.  One of the last one is the generation of the assembly chain from its Abstract Syntax Tree (AST).  This document tries to explain the mechanism and low-level integration to the assembly chain.

## Definition

An assembly chain is a list of operations, with each operation so limited it cannot be divided in smaller operations. Operations are small pieces of a script that have a very narrow and limited responsibility.

The important part of this definition is that "operations cannot be broken into smaller operations".  In other words, this is the lower level of a script.  If the script is paused, it can restart at a given operation.  This, however, should not break the script logic.

## Example

Here's a very basic usage.  Considering the code:

    data = 136

... which will be generated as the following tokens: `[ID('data'), SYMBOL(=), INT(136)]`.  This in turn will generate the following Abstract Syntax Tree:

    Assignment(data = Int(136))

The role of the assembly is to put it in a linar list of operations.  With this simple Abstract Syntax Tree, the assembly will create something like this:

    CONST 136
    STORE 'data'

These two operations represent how the program will run:

1. First 136 is pushed onto the stack of value.  We'll talk about the [stack](#stack-and-variables) in more details in another section.
2. Next, the variable of name 'data' should be created.  Its value is expected to be onto the stack.  So `STORE` will remove the last entry from the stack and assign a variable named 'data' to it (136).

This is important: suppose, for any reason, the program stops between line 1 and 2, that is to say, when 136 has been placed onto the stack but before the variable was created.  If the assembly and the stack are saved and the script continues later, then no logic error will occur.  This concept of potential pauses is extremely important and was a requirement from the start.

## Stack and variables

You will hear a lot about the stack in this document.  What is it in specific terms?  It contains the values used by the program.  As you'll see next, almost every expression (operation) retrieves something from the stack or put something onto it.  The stack is a "last-in-first-out" queue.  So if you put 5, then 10 onto the stack, and ask the stack the most recent value (MRV), it will return 5 (which was first added) and remove it from the stack.  So asking the stack's MRV again will produce 10.

The stack is extremely important to the assembly.  Operations almost always affect the stack and they are meant to manipulate it easily and flawlessly.  If the script should pause for any reason, the assembly can be stored with the next operation to be executed and the current stack.  Both data can be used to logically pause a script and restart it later.

If you want to dive into the low-level script system, you will most definitely have to read the assembly and emulate the stack at each line.  Examples are provided in the following sections to try and understand how both things are related.

Finally note the term "most recent value" (MRV).  This will be used a lot in this document.  The most recent value is the one that will be obtained from the stack.  The MRV is the first one that was added.  Remember, first in, first out.

What about variables?  Variables are stored in a different dictionary.  Variables aren't the stack and the stack doesn't contain variables, except variable values whenever necessary.

## List of expressions

An assemby chain is built out of expressions.  An expression is a very simple operation.  You already saw two of them: `CONST` and `STORE`.  In practice, each expression is stored in a separate module in the `scripting.assembly` package.  For instance, `STORE` resides in `scripting.assembly.store`.  Notice that expressions use capitalized names, but the module names follow the Python naming convention.

| Operation           | Module        | Arguments               | Short description                         |
|---------------------|---------------|-------------------------|-------------------------------------------|
| [ADD](#add)         | 'add.py'      | None                    | Add the two MRVs from the stack.          |
| [CALL](#call)       | 'call.py'     | Number of arguments.    | Call a function with its arguments.       |
| [CONST](#const)     | 'const.py'    | Any value.              | Put the value onto the stack.             |
| [DIV](#div)         | 'div.py'      | None                    | Divide the firrst MRV by the second MRV.  |
| [EQ](#eq)           | 'eq.py'       | None                    | Compare MRV1 == MRV2, push result.        |
| [GOTO](#goto)       | 'goto.py'     | Line to jumpp to.       | Jump to a given line/expression.          |
| [IFFALSE](#iffalse) | 'iffalse.py'  | Line to jump to.        | Jump to line if MRV is false.             |
| [IFTRUE](#iftrue)   | 'iftrue.py'   | Line to jump to.        | Jump to line if MRV is true.              |
| [LE](#le)           | 'le.py'       | None                    | Compare MRV1 < MRV2, push result.         |
| [LT](#lt)           | 'lt.py'       | None                    | Compare MRV1 <= MRV2, push result.        |
| [MUL](#mul)         | 'mul.py'      | None                    | Multiply the firrst MRV by the second.    |
| [NE](#ne)           | 'ne.py'       | None                    | Compare MRV1 != MRV2, push result.        |
| [NEG](#neg)         | 'neg.py'      | None                    | Negate MRV, usually a number.             |
| [NOT](#not)         | 'bool_not.py' | None                    | Reverse a MRV as a boolean.               |
| [STORE](#store)     | 'store.py'    | Variable name.          | Variable is assigned, MRV is the value.   |
| [SUB](#sub)         | 'sub.py'      | None                    | Subtract the firrst MRV with the second.  |
| [VALUE](#value)     | 'value.py'    | Variable name.          | Put this variable's value into the stack. |

### ADD

File: scripting/assembly/add.py

Put the two most recent values from the stack, add them up and place the result back into the stack.

ADD will perform four operations:

1. Remove the most recent value (MRV) from the stack.
2. Remove the next most recent value (MRV) from the stack.
3. Add the two values up.
4. Put the result back onto the stack.

Therefore, this assembly chain:

    CONST 3
    CONST 9
    ADD

Will place the value 12 onto the stack.

| Line | Operation          | Stack                  |
|------|--------------------|------------------------|
| 1    | `CONST 3`          | `[3]`                  |
| 2    | `CONST 9`          | `[3, 9]`               |
| 3    | `ADD`              | `[12]`                 |

ADD is mostly used by the `+` symbol.  The `Add` Abstract Syntax Tree will produce these operations:

1. Compute the left part of the symbo.
2. Compute the right part of the symbol.
3. Place the `ADD` operation in the assembly chain.

See 'scripting/ast/arithmetic.py', class `AddOp`, method `compute`.

### CALL

File: scripting/assembly/call.py

Read arguments from the stack and call the callable.

Arguments:

* The number of arguments to read from the stack.

CALL will perform four operations:

1. Read N arguments from the stack with any value.
2. Read one more element from the stack which should contain the callable object (function or method).
3. Execute the function with the arguments.
4. Put the result of the callable into the stack.

CALL will expect the number of arguments to read from the stack.  Here's one very simple example using a function called `add` (this is not a true example, there is no function of that name):

    add(3, 4)

In terms of assembly, the following will occur:

    1 CONST <function add...>
    2 CONST 3
    3 CONST 4
    4 CALL(2)

In other words, first we place the callable itself (the function `add` in this case) onto the stack.  Then we place each argument onto the stack.  Finally we execute `CALL` and tell it to read 2 arguments.

| Line | Operation          | Stack                  |
|------|--------------------|------------------------|
| 1    | `CONST <add>`      | `[<add>]`              |
| 2    | `CONST 3`          | `[3, <add>]`           |
| 3    | `CONST 4`          | `[4, 3, <add>]`        |
| 4    | `CALL(2)`          | `[7]`                  |

As you would expect, `CALL` is used to call functions.  The decision has been made to only receive the number of arguments and read values and callable from the stack.  This is because a function could call another function and expect its return value as argument too.  This allows for a clean chain of function calls.  Again, each function could decide to "pause" the script without breaking the logic.

### DIV

File: scripting/assembly/div.py

Put the two most recent values from the stack, divide the second by the first, and place the result back into the stack.

DIV will perform four operations:

1. Remove the most recent value (MRV) from the stack (value2).
2. Remove the next most recent value (MRV) from the stack (value1).
3. Divide value1 by value2.
4. Put the result back onto the stack.

Therefore, this assembly chain:

    CONST 4
    CONST 12
    DIV

Will place the value 3 onto the stack.

| Line | Operation          | Stack                  |
|------|--------------------|------------------------|
| 1    | `CONST 4`          | `[4]`                  |
| 2    | `CONST 12`         | `[4, 12]`              |
| 3    | `DIV`              | `[3]`                  |

DIV is mostly used by the `/` symbol.  The `Div` Abstract Syntax Tree will produce these operations:

1. Compute the left part of the symbo.
2. Compute the right part of the symbol.
3. Place the `DIV` operation in the assembly chain.

See 'scripting/ast/arithmetic.py', class `DivOp`, method `compute`.

### MUL

File: scripting/assembly/mul.py

Put the two most recent values from the stack, multiply them and place the result back into the stack.

MUL will perform four operations:

1. Remove the most recent value (MRV) from the stack.
2. Remove the next most recent value (MRV) from the stack.
3. Multiply the two values.
4. Put the result back onto the stack.

Therefore, this assembly chain:

    CONST 3
    CONST 9
    MUL

Will place the value 27 onto the stack.

| Line | Operation          | Stack                  |
|------|--------------------|------------------------|
| 1    | `CONST 3`          | `[3]`                  |
| 2    | `CONST 9`          | `[3, 9]`               |
| 3    | `MUL`              | `[27]`                 |

MUL is mostly used by the `*` symbol.  The `Mul` Abstract Syntax Tree will produce these operations:

1. Compute the left part of the symbo.
2. Compute the right part of the symbol.
3. Place the `MUL` operation in the assembly chain.

See 'scripting/ast/arithmetic.py', class `MulOp`, method `compute`.

### SUB

File: scripting/assembly/sub.py

Put the two most recent values from the stack, subtract the second to the first, and place the result back into the stack.

SUB will perform four operations:

1. Remove the most recent value (MRV) from the stack (value2).
2. Remove the next most recent value (MRV) from the stack (value1).
3. Subtract value2 to value1 (do `value1 - value2`).
4. Put the result back onto the stack.

Therefore, this assembly chain:

    CONST 15
    CONST 5
    SUB

Will place the value 10 onto the stack.

| Line | Operation          | Stack                  |
|------|--------------------|------------------------|
| 1    | `CONST 15`         | `[15]`                 |
| 2    | `CONST 5`          | `[15, 5]`              |
| 3    | `SUB`              | `[10]`                 |

SUB is mostly used by the `-` symbol when it is part of a binary operation.  The `Sub` Abstract Syntax Tree will produce these operations:

1. Compute the left part of the symbo.
2. Compute the right part of the symbol.
3. Place the `SUB` operation in the assembly chain.

**WARNING**: the minus sign can also be used as a unary operator, like `-(3 + 4)`.  In this context, SUB is not used.  Instead, [NEG](#neg) is called to negate the result of the operation.

See 'scripting/ast/arithmetic.py', class `SubOp`, method `compute`.

## Complete script

Obviously, a script contains a lot of instructions.  A line (as a str) might be translated into a lot of assembly expressions. so learning to read the assembly chain can be complicated.  Here are a few examples:

### Assigning an operation

To start with a simple example, let's see the assembly chain generated for the following instructions:

    result = 3 + 4

This is a relatively simple instruction that generatees the following assembly chain:

    0* CONST 3
    1  CONST 4
    2  ADD
    3  STORE 'result'

So it has 4 lines: `3` is placed onto the stack, `4` is placed onto the stack, both values are removed from the stack and added, `7` is placed onto the stack and then a variable of name 'result' is assigned to `7`.  You can see the logic here, though the assembly chain looks a little backward at first glance.

Let's see a more complicated use case:

    result = (4 + 8) / 2

This operation is a bit more complicated, involving two operators.  This will generate the following assembly chain:

    0* CONST 4
    1  CONST 8
    2  ADD
    3  CONST 2
    4  DIV
    5  STORE 'result'

You might get used to how the assembly chain is produced at this point.  First 4 and 8 are added, then 2 is placed onto the stack, then the MRV (2) divides the next MRV (12) and the result is pushed onto the stack.  So 'result' is assigned 6.

### Conditions

Conditions are more complex by definition.  We'll walk through the different usee cases.

#### A simple if block

Let's see a simple example first, using just an `if` statement.  Assuming we4 have created a variable 'result' of value 6:

    if result == 6.0 then
        result = 32
    end

This will generate the following assembly chain:

    0* VALUE 'result'
    1  CONST 6.0
    2  EQ
    3  IFFALSE 6
    4  CONST 32
    5  STORE 'result'

Let's examine line by line:

1. First is the condition itself.  We begin by putting the value of the 'result' variable onto the stack, which is 6.0.
2. Next we put another 6.0 onto the stack.
3. We compare that both MRVs are equal.  [EQ](#eq) will put the result, as a boolean, onto the stack.
4. If the result is false, jump to the line 6.  Note, this line doesn't exist, the assembly chain stops at line 5, but if we had something after the condition, this would be executed.
5. We place 32 onto the stack.
6. And we assign 'result' to it.

So after this chain, 'result' should be 32.

The call to [IFFALSE](#iffalse) is important here? if the condition is not true, then we jump directly to the end of the condition block.

#### An if and else block

Let's now see a block with an `else` alternative:

    if result < 10 then
        result = 20
    else
        result = 50
    end

This will create a more complex assembly chain:

    0* VALUE 'result'
    1  CONST 10
    2  LT
    3  IFFALSE 7
    4  CONST 20
    5  STORE 'result'
    6  GOTO 9
    7  CONST 50
    8  STORE 'result'

The beginning is quite similar to our first use case:

1. We retrieve the value of 'result'.
2. We place 10 onto the stack.
3. We check that the variable is lower than 10.  It's not the case if you've followed the same example.
4. So [IFFALSE](#iffalse) again checks that, should the MRV be false, we should jump to line 7.  Notice that line 7 is our `else` block.
5. We put 20 onto the stack.
6. We assign the variable 'result'.
7. And we jump to the line 9.  Line 9 is the end of the condition.  So if the condition was true, we should execute only the instructions right under the `if` block and jump to the end of the block after that.
8. Here's our line 7.  So our `else` block.  We push 50 onto the stack.
9. We assign it to the variable 'result'.

And that's it.  You can test this assembly chain with several values of 'result'.  You should obtain the modification that matches the condition.

#### A complex condition

The authori of the script can also use the `and` and `or` to link conditions.  We'll see instead a simple link of operators that does look more understandable.  The principle is the same.

    if 0 < result <= 100 then
        result = 100
    else
        result = 0
    end

Our initial condition was more complex: if 'result' is between 0 and 100 (not including 0).  Let's see the generated assembly chain:

     0* CONST 0
     1  VALUE 'result'
     2  LT
     3  IFFALSE 7 False
     4  VALUE 'result'
     5  CONST 100
     6  LE
     7  IFFALSE 11
     8  CONST 100
     9  STORE 'result'
    10  GOTO 13
    11  CONST 0
    12  STORE 'result'

Let's focus on the first lines of this assembly chain, as the end should look quite familiar.

1. We place 0 onto the stack.
2. We place the value of the 'result' variable.
3. We compare them using the `<=` operator.  After this line, either `True` or `False` should be written onto the stack.
4. Then we have a strange [IFFALSE](#iffalse): we should jump to line 7 if the value is False... but there's another argument.  In this case, if the second argument of `IFFALSE` is `False` (the default is `True`), `IFFALSE` places the value back onto the stack.  So `IFFALSE` will get the boolean from the stack and put it back there.  Why is this necessary?  If you follow along, you see that `IFFALSE` should jump to line 7.  What is line 7?  Another `IFFALSE`!  Which jumps to line 11.  So the second one is a stepping stone of sort.  We have to put the boolean back into the stack.  The `IFFALSE` at line 3 is just here to check whether `0 < result` is `False`.  If so, no need to test the rest of the condition, so jump ahead.

The next of the lines shouldn't surprise you.  Notice though that with a program which is still pretty simple, we already have 13 lines in the assembly chain and some instructions do not look really straightforward.  The assembly chain is not primarly meant to be read and analyzed, it's meant to run fast, but if you need to read it, be prepared to handle even longer chains.

