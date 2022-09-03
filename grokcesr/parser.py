import re


# Used to describe the value of a token
tt_bof = 0
tt_eof = 1
tt_begin_obj = '{'
tt_end_obj = '}'
tt_begin_bin = 4
tt_end_bin = 5
tt_lf = 6
tt_blob = 7
tt_whitespace = 8
tt_key = 9
tt_str_value = 10
tt_num_value = 11
tt_reserved_value = 12
tt_begin_arr = '['
tt_end_arr = ']'
tt_comma = ','
tt_colon = ':'


# Allow reverse lookup of token names by token type values. Useful
# for debugging.
x = {}
for k in [k for k in globals().keys() if k.startswith('tt_')]:
    x[globals()[k]] = k
tt_names_by_value = x
del(x)


def get_tt_name(tt_value):
    g = globals()
    for name in _tt_names:
        if g[name] == tt_value:
            return name


# Used to parse json
key_pat = re.compile(r'([\r\n\t ]*)("[^"]*")([\r\n\t ]*):([\r\n\t ]*)')
reserved_pat = re.compile(r'null|true|false')
num_pat = re.compile(r'(-?)(\d+(?:[.]\d+)?)(e\d+)?')
comma_pat = re.compile(r'([\r\n\t ]*),')
end_of_obj_pat = re.compile(r'([\r\n\t ]*)}')
end_of_arr_pat = re.compile(r'([\r\n\t ]*)\]')


def parse_json_arr(state):
    # function starts pointing at [; consume that.
    state.offset += 1
    must_end = False
    # Loop over all the elements of the array
    while not state.done:
        # Check to see if the array is ending.
        m = end_of_arr_pat.match(state.cesr, state.offset)
        if m:
            whitespace = state.until(m.end() - 1)
            if whitespace:
                yield VariableContentToken(tt_whitespace, whitespace)
            state.offset += 1
            return
        elif must_end:
            raise Exception("expected end of array at %d" % state.offset)
        # Consume one value in the array.
        for token in parse_json_val(state):
                yield token
        # See if the array is continued. If it is, consume the comma and emit tokens as needed.
        m = comma_pat.match(state.cesr, state.offset)
        if m:
            yield VariableContentToken(tt_whitespace, state.until(m.end() - 1))
            yield UniformContentToken(tt_comma)
            state.offset += 1
        else:
            must_end = True


def parse_json_val(state):
    func = None
    c = state.next
    if c == '{':
        func, b, e = parse_json_obj, UniformContentToken(tt_begin_obj), UniformContentToken(tt_end_obj)
    elif c == '[':
        func, b, e = parse_json_arr, UniformContentToken(tt_begin_arr), UniformContentToken(tt_end_arr)
    else:
        tt = None
        m = num_pat.match(state.cesr, state.offset)
        if m:
            tt = tt_num_value
        else:
            m = reserved_pat.match(state.cesr, state.offset)
            if m:
                tt = tt_reserved_value
        if m:
            yield VariableContentToken(tt, state.until(m.end()))
        else:
            raise Exception("malformed json at %d" % state.offset)
    if func:
        for t in run_parse_function(func, b, e, state):
            yield t


def parse_json_obj(state):
    # function starts pointing at {; consume that.
    state.offset += 1
    must_end = False
    # Loop over all the properties of the object
    while not state.done:
        m = end_of_obj_pat.match(state.cesr, state.offset)
        if m:
            whitespace = state.until(m.end() - 1)
            if whitespace:
                yield VariableContentToken(tt_whitespace, whitespace)
            state.offset += 1
            return
        elif must_end:
           raise Exception("expected end of obj at %d" % state.offset)
        m = key_pat.match(state.cesr, state.offset)
        if not m:
            raise Exception("malformed json at %d" % state.offset)
        state.offset = m.end()
        if m.group(1):
            yield VariableContentToken(tt_whitespace, m.group(1))
        yield VariableContentToken(tt_key, m.group(2))
        if m.group(3):
            yield VariableContentToken(tt_whitespace, m.group(3))
        yield UniformContentToken(tt_colon)
        if m.group(4):
            yield VariableContentToken(tt_whitespace, m.group(4))
        c = state.next
        if c == '"':
            i = state.cesr.find('"', state.offset + 1)
            yield VariableContentToken(tt_str_value, state.until(i + 1))
        else:
            for token in parse_json_val(state):
                yield token
        m = comma_pat.match(state.cesr, state.offset)
        if m:
            whitespace = state.until(m.end() - 1)
            if whitespace:
                yield VariableContentToken(tt_whitespace, state.until(m.end() - 1))
            yield UniformContentToken(tt_comma)
            state.offset += 1
        else:
            must_end = True


def run_parse_function(func, beginner, ender, state):
    """
    Accept an arbitrary generator that consumes a particular type of content
    and yields (token_type, token) tuples, plus begin and end tokens, yield
    the begin token, then call the generator repeatedly until it's exhausted
    or an exception occurs, then yield the end token. This embodies a pattern
    for using all our content-parsing functions.

    :param func: A function that parses the appropriate type of content.
    :param beginner: token that marks the beginning of this content
    :param ender: token that marks the end of this content
    :param state: Holds accumulated state like string and offset.
    """
    try:
        yield beginner
        for token in func(state):
            yield token
    finally:
        yield ender


def parse_bin(state):
    i = state.offset
    j = state.cesr.find('{', i)
    if j == -1:
        j = state.end
    yield VariableContentToken(tt_blob, state.until(j))


def parse_cesr(state):
    while not state.done:
        c = state.next
        # Look at the tritet
        if c == '{':
            b, e, func = UniformContentToken(tt_begin_obj), UniformContentToken(tt_end_obj), parse_json_obj
        else:
            b, e, func = LogicalToken(tt_begin_bin), LogicalToken(tt_end_bin), parse_bin
        for token in run_parse_function(func, b, e, state):
            yield token


def parse(cesr):
    """
    Consume CESR and yield a series of (token_type, token) tuples that explains what it contains.
    """
    state = ParseState(cesr)
    for token in run_parse_function(parse_cesr, LogicalToken(tt_bof), LogicalToken(tt_eof), state):
        yield token


class ParseState:
    def __init__(self, cesr):
        self.cesr = cesr
        self.end = len(self.cesr)
        self.offset = 0

    @property
    def done(self):
        return self.offset >= self.end

    @property
    def next(self):
        return self.cesr[self.offset]

    def until(self, i):
        fragment = self.cesr[self.offset:i]
        self.offset = i
        return fragment

    def __str__(self):
        i = max(0, self.offset - 8)
        prefix = "..." if i > 0 else ""
        j = min(self.end, self.offset + 8)
        suffix = "..." if j < self.end else ""
        return prefix + self.cesr[i:self.offset] + "➤" + self.cesr[self.offset:j] + suffix


class LogicalToken:
    """
    A token that represents a change in logical structure, without having any
    associated content. The token for beginning and end of a file are good
    examples.
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        global tt_names_by_value
        return "(%s)" % tt_names_by_value[self.value]


class UniformContentToken:
    """
    A token that has associated content, but the content never varies. Thus, the
    content reveals the token type.
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class VariableContentToken:
    """
    A token that has content, where the content is not enough to reveal the type
    of the token.
    """
    def __init__(self, typ, value):
        self.typ = typ
        self.value = value

    def __str__(self):
        return "%s, value = %s" % (tt_names_by_value[self.typ], self.value)
