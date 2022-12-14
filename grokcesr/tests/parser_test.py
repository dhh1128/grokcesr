from pytest import raises

from ..parser import *

L = LogicalToken.__class__
U = UniformContentToken.__class__
V = VariableContentToken.__class__


def _comparable_str(t):
    if isinstance(t, int):
        return tt_names_by_value[t]
    elif isinstance(t, str):
        return t
    elif isinstance(t, tuple):
        return str((tt_names_by_value[t[0]], t[1]))
    elif isinstance(t, VariableContentToken):
        return _comparable_str((t.typ, t.value))
    else:
        return _comparable_str(t.value)


def _assert_parse(fragment, expected, filter=None):
    tokens = [t for t in parse(fragment)]
    if filter:
        tokens = filter(tokens)
    tokens = [_comparable_str(t) for t in tokens]
    expected = [_comparable_str(t) for t in expected]
    assert tokens == expected


def assert_parse(fragment, *expected):
    _assert_parse(fragment, expected)


def assert_in_obj(obj_content, *expected):
    _assert_parse("{" + obj_content + "}", expected, lambda tokens: tokens[2:-2])


def test_parse_basic():
    assert_parse('', tt_bof, tt_eof)
    assert_parse('{}', tt_bof, '{', '}', tt_eof)
    assert_parse('abc', tt_bof, tt_begin_bin, (tt_blob, "abc"), tt_end_bin, tt_eof)
    assert_parse('{}abc', tt_bof, '{', '}', tt_begin_bin, (tt_blob, "abc"), tt_end_bin, tt_eof)
    assert_parse('abc{}', tt_bof, tt_begin_bin, (tt_blob, "abc"), tt_end_bin, '{', '}', tt_eof)


def test_one_key():
    assert_in_obj('"a":1', (tt_key, '"a"'), tt_colon, (tt_num_value, '1'))
    assert_in_obj('"a":"b"', (tt_key, '"a"'), tt_colon, (tt_str_value, '"b"'))
    assert_in_obj('"a":null', (tt_key, '"a"'), tt_colon, (tt_reserved_value, 'null'))


def test_floating_point_value():
    assert_in_obj('"a":1.3', (tt_key, '"a"'), tt_colon, (tt_num_value, '1.3'))
    assert_in_obj('"a":1.3e7', (tt_key, '"a"'), tt_colon, (tt_num_value, '1.3e7'))


def test_obj_two_keys_numeric():
    assert_in_obj('"a":1,"b":2',
        (tt_key, '"a"'), tt_colon, (tt_num_value, '1'), tt_comma,
        (tt_key, '"b"'), tt_colon, (tt_num_value, '2')
    )


def test_obj_two_keys_reserved():
    assert_in_obj('"a":true,"b":false',
        (tt_key, '"a"'), tt_colon, (tt_reserved_value, 'true'), tt_comma,
        (tt_key, '"b"'), tt_colon, (tt_reserved_value, 'false')
    )


def test_obj_two_keys_str_num():
    assert_in_obj('"a":"true","b":1.3e7',
        (tt_key, '"a"'), tt_colon, (tt_str_value, '"true"'), tt_comma,
        (tt_key, '"b"'), tt_colon, (tt_num_value, '1.3e7')
    )


def test_array():
    assert_in_obj('"a":[]', (tt_key, '"a"'), tt_colon, '[', ']')
    assert_in_obj('"a":[1,null]', (tt_key, '"a"'), tt_colon, '[', (tt_num_value, '1'), tt_comma, (tt_reserved_value, "null"), ']')


def test_whitespace():
    assert_in_obj('\n  "a" :\t0',
        (tt_whitespace, '\n  '), (tt_key, '"a"'), (tt_whitespace, ' '), tt_colon,
        (tt_whitespace, '\t'), (tt_num_value, '0'))
    assert_in_obj('\r  "a"\r:\t[\n0 ,\t12345 ]',
        (tt_whitespace, '\r  '), (tt_key, '"a"'), (tt_whitespace, '\r'), tt_colon,
        (tt_whitespace, '\t'), tt_begin_arr,
        (tt_whitespace, '\n'), (tt_num_value, '0'), (tt_whitespace, ' '), tt_comma,
        (tt_whitespace, '\t'), (tt_num_value, '12345'), (tt_whitespace, ' '),
        tt_end_arr)


def assert_error(cesr, emsg):
    try:
        # Consume tokens to allow exception to be raised.
        for t in parse(cesr):
            pass
    except Exception as e:
        assert emsg in str(e)
        return
    raise Exception('Expected error message containing "%s" but got no error.' % emsg)


def test_nested():
    assert_in_obj('"a":[{"b":0, "c": false,  "d":{}}]',
        (tt_key, '"a"'), tt_colon, '[',
        tt_begin_obj, (tt_key, '"b"'), tt_colon, (tt_num_value, '0') , tt_comma,
        (tt_whitespace, ' '), (tt_key, '"c"'), tt_colon, (tt_whitespace, ' '),
        (tt_reserved_value, 'false'), tt_comma, (tt_whitespace, '  '),
        (tt_key, '"d"'), tt_colon, tt_begin_obj, tt_end_obj, tt_end_obj, tt_end_arr)


def test_open():
    assert_error('{', "expected end of JSON obj")
    assert_error('{"a":1', "expected end of JSON obj")
    assert_error('{"a":[}', "expected JSON value")