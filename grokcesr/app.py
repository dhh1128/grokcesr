import re
import sys

from .parser import parse
from .printer import pretty_print

help_pat = re.compile(r'[?]|--?h(elp)?', re.I)


def main(argv):
    if len(argv) < 2 or len(argv) == 2 and help_pat.match(argv[1]):
        print('cesrparse file [file...]\n')
    else:
        try:
            with open(argv[1], "rb") as f:
                cesr = f.read()
                for token in parse(cesr):
                    pretty_print(token, sys.stdout)
        except:
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main(sys.argv)