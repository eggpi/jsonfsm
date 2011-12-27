#-*- coding: utf-8 -*-

NOT_PARSED_YET = object()

class JSONParseError(Exception):
    pass

def coroutine(f):
    def start(*args, **kwargs):
        cr = f(*args, **kwargs)
        cr.next()
        return cr
    return start

@coroutine
def string_fsm():
    '''
    A coroutine implementing a finite state machine for parsing JSON strings.
    Accepts the string one character at a time, and yields NOT_PARSED_YET until
    the string has been successfully parsed.
    Once the JSON string has been parsed, yields the corresponding Python
    string. The coroutine can't be used after that.
    May raise JSONParseError on malformed strings.
    Expects data with no leading or trailing whitespace (i.e., the first and
    last input characters should be ").
    '''

    value = []

    c = (yield NOT_PARSED_YET)
    if c != '"':
        raise JSONParseError("JSON strings must start with a quote")

    while True:
        c = (yield NOT_PARSED_YET)
        if c == '"':
            # end of string
            break
        elif c == '\\':
            c = (yield NOT_PARSED_YET)
            if c == 'u':
                # unicode 4-digit hexadecimal
                hexval = ""
                for i in range(4):
                    hexval += (yield NOT_PARSED_YET)

                value.append(unichr(int(hexval, 16)))
        else:
            value.append(c)

    yield ''.join(value)

@coroutine
def number_fsm():
    '''
    A coroutine implementing a finite state machine for parsing JSON numbers.
    Accepts the characters of the number string one at a time.
    Since numbers don't have delimiters, this coroutine always yields partial
    results when they are available. Therefore, when parsing, e.g., 12.45, this
    coroutine yields 1.0, 12.0, NOT_PARSED_YET, 12.4 and finally 12.45 before
    stopping.
    Always returns JSON numbers as Python floats and may raise JSONParseError
    for invalid numbers.
    Expects input characters with no leading or trailing whitespace.
    '''

    digits = []

    # we actually only validate the number, and let Python's builtin float()
    # do the conversion inside this function
    def build_number():
        number_string = ''.join(digits)
        return float(number_string)

    c = (yield NOT_PARSED_YET)
    if c == '-':
        digits.append(c)
        c = (yield NOT_PARSED_YET)

    # parse integer part
    # this must either be a single zero or a non-zero digit followed by a
    # sequence of other digits
    if not c.isdigit():
        raise JSONParseError("Unexpected leading nondigit: %s" % c)

    digits.append(c)
    if c != '0':
        while True:
            c = (yield build_number())
            if c.isdigit():
                digits.append(c)
            else:
                break
    else:
        c = (yield 0)

    if c.isdigit():
        raise JSONParseError("Unexpected digit: %s" % c)

    if c == '.':
        digits.append(c)
        c = (yield NOT_PARSED_YET)
        # parse fractional part, if any
        while True:
            if not c.isdigit():
                if c.lower() == 'e':
                    break
                raise JSONParseError("Unexpected character in number: %s" % c)
            digits.append(c)
            c = (yield build_number())

    assert not c.isdigit()

    # handle scientific notation
    if c.lower() == 'e':
        digits.append(c)

        c = (yield NOT_PARSED_YET)
        if c == '-':
            digits.append(c)
            c = (yield NOT_PARSED_YET)

        if not c.isdigit():
            raise JSONParseError("Unexpected character in number: %s" % c)

        while c.isdigit():
            digits.append(c)
            c = (yield build_number())

    else:
        raise JSONParseError("Unexpected character in number: %s" % c)

    yield build_number()

@coroutine
def array_fsm():
    '''
    A coroutine implementing a finite state machine for parsing JSON arrays.
    Thie coroutine will yield NOT_PARSED_YET until the array has been
    successfully parsed, at which point a Python list representing the array
    will be yielded.
    May raise JSONParseError for invalid objects.
    Expects input data with no leading or trailing whitespace, that is, the
    first input character must be [ and the last must be ].
    '''

    array = []

    c = (yield NOT_PARSED_YET)
    if c != '[':
        raise JSONParseError("Arrays must begin with [")

    while c != ']':
        c = (yield NOT_PARSED_YET)
        while c.isspace():
            c = (yield NOT_PARSED_YET)

        vp = value_fsm()
        value = NOT_PARSED_YET

        # look out for , and ] since they act as delimiters for numbers.
        while c not in (',', ']') or value is NOT_PARSED_YET:
            value = vp.send(c)
            c = (yield NOT_PARSED_YET)

        array.append(value)

    yield array

@coroutine
def object_fsm():
    '''
    A coroutine implementing a finite state machine for parsing JSON objects.
    This coroutine will yield NOT_PARSED_YET until the object has been
    successfully parsed, at which point a Python dictionary representing the
    object will be yielded.
    May raise JSONParseError for invalid objects.
    Expects input data without leading or trailing whitespace, that is, the
    first input character must be { and the last }.
    '''

    obj = {}

    c = (yield NOT_PARSED_YET)
    if c != '{':
        raise JSONParseError("Objects must begin with {")

    while c != '}':
        c = (yield NOT_PARSED_YET)
        while c.isspace():
            c = (yield NOT_PARSED_YET)

        # parse attribute key
        key = NOT_PARSED_YET
        sp = string_fsm()
        while key is NOT_PARSED_YET:
            key = sp.send(c)
            c = (yield NOT_PARSED_YET)

        while c.isspace():
            c = (yield NOT_PARSED_YET)

        if c != ':':
            raise JSONParseError("Missing : between attribute name and value")

        c = (yield NOT_PARSED_YET)
        while c.isspace():
            c = (yield NOT_PARSED_YET)

        # parse value
        vp = value_fsm()

        # look out for , and } since they act as delimiters for numbers
        while c not in (',', '}') or value is NOT_PARSED_YET:
            value = vp.send(c)
            c = (yield NOT_PARSED_YET)

        obj[key] = value

    yield obj

@coroutine
def value_fsm():
    '''
    A coroutine implementing a finite state machine for parsing an arbitrary
    JSON value.
    Expects the value to have no leading or trailing whitespace.
    '''

    @coroutine
    def string_matcher_fsm(match, retval):
        '''
        A simple finite state machine for string matching.
        '''

        while match:
            if (yield NOT_PARSED_YET) == match[0]:
                match = match[1:]
            else:
                raise JSONParseError

        yield retval

    # try all available parsers on the input data, only one should
    # succeed.
    parsers = [
        number_fsm(),
        object_fsm(),
        array_fsm(),
        string_fsm(),
        string_matcher_fsm("null", None),
        string_matcher_fsm("false", False),
        string_matcher_fsm("true", True),
    ]

    # find the correct parser (all others should fail in the first character)
    c = (yield NOT_PARSED_YET)
    for p in parsers:
        try:
            value = p.send(c)
        except JSONParseError:
            pass
        else:
            break
    else:
        raise JSONParseError("Failed to parse JSON value")

    while True:
        value = p.send((yield value))

def loads(json, encoding = "utf-8"):
    '''
    Load a JSON object from a string.
    '''

    json = unicode(json, encoding)
    parser = value_fsm()
    for c in json.strip():
        ret = parser.send(c)

    return ret
