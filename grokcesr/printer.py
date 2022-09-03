from .parser import *

header = """<html>
<head>
<style>
body { color: #444; padding: 20px;}
pre {
    counter-reset: line;
}
code {
    counter-increment: line;
}
code:before{
    display: inline-block;
    width: 2em;
    text-align: right;
    content: counter(line);
    -webkit-user-select: none;
    padding-right: 1em;
    color: #ccc;
}
</style>
</head>
<body>
<pre>"""

footer = """</pre>
</body>
</html>
"""


def pretty_print(token, fout):
    if isinstance(token, VariableContentToken) or isinstance(token, UniformContentToken):
        out = token.value
    elif isinstance(token, LogicalToken):
        if token.value == tt_bof:
            out = header
        elif token.value == tt_eof:
            out = footer
        else:
            out = ""
    fout.write(out)
