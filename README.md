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
