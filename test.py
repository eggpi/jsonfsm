#-*- coding: utf-8 -*-

import jsonfsm
import unittest

class TestString(unittest.TestCase):
    def setUp(self):
        self.python_string = u"• This is a test string."
        self.json_string = '"' + self.python_string + '"'

        self.another_python_string = u"Isto é uma string de teste."
        self.another_json_string = '"' + self.another_python_string + '"'

        self.multiline_json_string = '"Never been good enough\nTo write Haiku."'

    def test_decode(self):
        res = jsonfsm.loads(self.json_string)

        self.assertTrue(isinstance(res, unicode))
        self.assertEquals(res, self.python_string)

    def test_surrounding_quotes(self):
        # missing both "
        self.assertRaises(jsonfsm.JSONParseError,
                          jsonfsm.loads,
                          self.json_string[1:][:-1])

        # missing trailing "
        self.assertRaises(jsonfsm.JSONParseError,
                          jsonfsm.loads,
                          self.json_string[1:])

        # missing leading "
        self.assertRaises(jsonfsm.JSONParseError,
                          jsonfsm.loads,
                          self.json_string[:-1])

    def test_character_encoding(self):
        l1_encoded = self.another_json_string.encode("latin1")
        res = jsonfsm.loads(l1_encoded, "latin1")

        self.assertEquals(res, jsonfsm.loads(self.another_json_string))
        self.assertEquals(res, self.another_python_string)

    def test_control_characters(self):
        self.assertTrue('\n' in jsonfsm.loads(self.multiline_json_string))

        self.assertEquals(jsonfsm.loads('"\u2022"'), u"•")

        self.assertRaises(jsonfsm.JSONParseError,
                          jsonfsm.loads,
                          self.json_string[:-1] + r'\k"')

class TestNumber(unittest.TestCase):
    def setUp(self):
        self.numbers = (
            "1",
            "0",
            "0.04",
            "1.02",
            "35.2e1",
            "52e-2",
        )

        self.invalid = (
            "01",
            "00",
            ".45",
            "1e-0.2",
            "0.01e",
        )

    def test_valid_numbers(self):
        for n in self.numbers:
            self.assertEquals(jsonfsm.loads(n), float(n))

    def test_invalid_numbers(self):
        for invalid in self.invalid:
            self.assertRaises(jsonfsm.JSONParseError,
                              jsonfsm.loads,
                              invalid)

class TestArray(unittest.TestCase):
    def setUp(self):
        self.valid = (
            ('[]', []),
            ("[1]", [1.0]),
            ("[ 1,   2,  3]", [1.0, 2.0, 3.0]),
            ('[   "a string with ]"]', [u"a string with ]"]),
            ('[ ["nested array"], 1]', [[u"nested array"], 1.0]),
        )

        self.invalid = (
            "[,]",
            "[1,]",
        )

    def test_valid_arrays(self):
        for json, expected in self.valid:
            self.assertEquals(jsonfsm.loads(json), expected)

    def test_invalid_arrays(self):
        for json in self.invalid:
            self.assertRaises(jsonfsm.JSONParseError,
                              jsonfsm.loads,
                              json)

class TestObject(unittest.TestCase):
    def setUp(self):
        self.valid = (
            ('{}', {}),
            ('{"one": 1}', {u"one": 1.0}),
            ('{ "one" :1, "two": 2}', {u"one":1.0, u"two":2.0}),
            ('{"delimiter": "}" }', {u"delimiter": u"}"}),
            ('{"nested": {"object": "here"}}', {u"nested": {u"object": u"here"}}),
        )

        self.invalid = (
            "{,}",
            '{"key":}',
            '{:"value"}',
            '{"extra" : "comma",}',
        )

    def test_valid_objects(self):
        for json, expected in self.valid:
            self.assertEquals(jsonfsm.loads(json), expected)

    def test_invalid_objects(self):
        for json in self.invalid:
            self.assertRaises(jsonfsm.JSONParseError,
                              jsonfsm.loads,
                              json)

class TestConformanceWithStdlib(unittest.TestCase):
    import glob
    import json

    def setUp(self):
        self.json_files = self.glob.glob("tests/*.json")

    def test_conformance(self):
        for json in self.json_files:
            with open(json) as infile:
                data = infile.read()
                self.assertEquals(jsonfsm.loads(data), self.json.loads(data))

if __name__ == "__main__":
    unittest.main()
