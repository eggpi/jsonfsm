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

if __name__ == "__main__":
    unittest.main()
