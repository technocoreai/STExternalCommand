About
=====

A Sublime Text 2 & 3 plugin for modifying buffers using external command output.

Installation
============

Preferred installation method is through [Package Control](https://sublime.wbond.net/). Search for "External Command".

Alternatively you can install this package by running the following in your `Packages` directory:

    git clone https://github.com/greneholt/SublimeExternalCommand/

Commands
========

Filter Through Command
----------------------

Pipes each non-empty selection through an external command and replaces contents of the selection with its output. If there are no non-empty selections, replaces the whole buffer.

To use, press *Selection* / *Filter Through Command* or use the command palette. You can also bind it to a hotkey:

    { "keys": ["…"], "command": "filter_through_command" }

Along with the *cmdline* argument explained below, this command also accepts a boolean *full_line* argument, which if set will expand each selection to the entire line before processing.

Insert Command Output
---------------------

For every selection, launches external command and inserts output at the start of the selection.

To use, press *Selection* / *Insert Command Output* or use the command palette. You can also bind it to a hotkey:

    { "keys": ["…"], "command": "insert_command_output" }


Notes
=====

External command will be executed asynchronously, so you can cancel it by activating it again. It will also be automatically canceled if you try to modify buffer contents, selections, or close the buffer.

Both commands accept an optional *cmdline* argument, so you can use them to quickly bind specific external commands. For example,
add this to your bindings to quickly add line numbers to selected text:

    { "keys": ["…"], "command": "filter_through_command", "args": { "cmdline": "cat -n" } }

License
=======

All of SublimeExternalCommand is licensed under the MIT license.

Copyright (c) 2011 Alexey Ermakov <zee@technocore.ru>

Copyright (c) 2013 Connor McKay

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
