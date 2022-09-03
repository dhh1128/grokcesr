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


def pretty_print(data):
    if isinstance(data, int):
        if data.type == header_symbol:
                print(header)
        elif data.type == footer_symbol:
                print(footer)
    elif isinstance(data, str):
        print(data)
    else:
        print(f"<code>{data}</code>")
