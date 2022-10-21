import message
import utils
import unittest

identify_msg = {"type": "IDENTIFY",
                "username": "José Arcadio Buendía"}


class MessagetTestCase(unittest.TestCase):
    def test_comparison(self):
        self.assertEqual(identify_msg, message.Message(identify_msg))

    def test_membership(self):
        self.assertIn("type", message.Message(identify_msg))

    def test_encoding(self):
        self.assertEqual(bytes('{"name": "José Arcadio Buendía"}', "utf-8"),
                         message.Message({"name":
                                          "José Arcadio Buendía"}).encoded)

    def test_from_encoding(self):
        self.assertEqual({"name": "José Arcadio Buendía"},
                         message.Message.from_encoded(
                             bytes('{"name": "José Arcadio Buendía"}', "utf-8")
                         ))

    def test_from_invalid_encoding(self):
        with self.assertRaises(utils.MessageException):
            message.Message.from_encoded(b'{foo: bar')

        with self.assertRaises(utils.MessageException):
            message.Message.from_encoded(
                b'["foo", {"bar": ["baz", null, 1.0, 2]}]'
            )
