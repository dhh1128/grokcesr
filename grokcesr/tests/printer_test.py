import io
import re

from ..printer import pretty_print, header, footer
from ..parser import parse


def print_all(cesr):
    f = io.StringIO()
    for token in parse(cesr):
        pretty_print(token, f)
    return f.getvalue()


def just_body(html):
    if html.startswith(header):
        html = html[len(header):]
    if html.endswith(footer):
        html = html[:-1*len(footer)]
    return html


def assert_printed(cesr, regex, body_only=True):
    html = print_all(cesr)
    if body_only:
        html = just_body(html)
    if not re.search(regex, html):
        print("HTML = %s" % html)
        raise Exception('Printed HTML didn\'t match regex "%s".' % regex)


def test_empty():
    assert_printed('', header.rstrip()[-5:] + r'[\r\n\t ]*' + footer.lstrip()[:5], False)