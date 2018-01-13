# erio

Erio is a toy language and interpreter for a language which I created in my
spare time years ago.

It's a basic imperitive language with a few primitives implemented.

Perhaps the most interesting thing about it is the way Python's generators are
used to set up a pipeline from the tokenizer to the parser to the interpreter,
so that execution of a statement happens as soon as the final character of the
statement has be read from input.

It also makes use of Python decorators to make declaring new language
primitives quick and easy.

## Supported

if, while, functions, recursion, arrays

## Not supported

Escape sequences, string concatenation

## Example program

```
def fib(n)
    if n == 0 or n == 1 then
        return n 
    else
        return fib(n - 1) + fib(n - 2)
    end-if
end-def

i = 0
while i < 10 do
    print(fib(i))
    print(" ")
    i = i + 1
end-while

```
