"""Test the behavir of command arguments."""

from command.args import CommandArgs, ArgumentError
from test.base import BaseTest

class TestCommandArgs(BaseTest):

    def test_text(self):
        """Test to parse one argument as text."""
        # Try to enter a single word
        args = CommandArgs()
        args.add_argument("text", dest="simple")
        namespace = args.parse("something")
        self.assertEqual(namespace.simple, "something")

        # Try to enter several words
        args = CommandArgs()
        args.add_argument("text")
        namespace = args.parse("something else")
        self.assertEqual(namespace.text, "something else")

    def test_word(self):
        """Test one or several words in arguments."""
        # Try to enter a single word
        args = CommandArgs()
        args.add_argument("word", dest="simple")
        namespace = args.parse("something")
        self.assertEqual(namespace.simple, "something")

        # Try to enter several words
        args = CommandArgs()
        args.add_argument("word", dest="first")
        args.add_argument("word", dest="second")
        namespace = args.parse("something else")
        self.assertEqual(namespace.first, "something")
        self.assertEqual(namespace.second, "else")

    def test_options(self):
        """Test options arguments."""
        # Try to enter a single option
        args = CommandArgs()
        options = args.add_argument("options")
        options.add_option("t", "title", dest="title")
        namespace = args.parse("title=ok")
        self.assertEqual(namespace.title, "ok")

        # Try again, but with two words in the title
        namespace = args.parse("title=a title")
        self.assertEqual(namespace.title, "a title")

        # Try short options
        namespace = args.parse("t=ok")
        self.assertEqual(namespace.title, "ok")

        # Try again, but with two words in the title
        namespace = args.parse("t=a title")
        self.assertEqual(namespace.title, "a title")

        # Try with several options
        args = CommandArgs()
        options = args.add_argument("options")
        options.add_option("t", "title", optional=False, dest="title")
        options.add_option("d", "description", dest="description")
        namespace = args.parse("title=ok d=a description")
        self.assertEqual(namespace.title, "ok")
        self.assertEqual(namespace.description, "a description")

        # Try again, but with two words in the title
        namespace = args.parse("title=a title description=something")
        self.assertEqual(namespace.title, "a title")
        self.assertEqual(namespace.description, "something")

        # Try short options
        namespace = args.parse("description=well t=ok")
        self.assertEqual(namespace.title, "ok")
        self.assertEqual(namespace.description, "well")

        # Try again, but with two words in the title
        namespace = args.parse("t=a title description=hi")
        self.assertEqual(namespace.title, "a title")
        self.assertEqual(namespace.description, "hi")

        # Test with word argument
        args = CommandArgs()
        args.add_argument("word")
        options = args.add_argument("options")
        options.add_option("t", "title", dest="title")
        options.add_option("d", "description", dest="description")
        namespace = args.parse("and d=something else title=ok")
        self.assertEqual(namespace.word, "and")
        self.assertEqual(namespace.title, "ok")
        self.assertEqual(namespace.description, "something else")

        # Test mandatory and optional options
        args = CommandArgs()
        options = args.add_argument("options")
        options.add_option("t", "title", default="nothing", dest="title")
        options.add_option("d", "description", dest="description")
        namespace = args.parse("d=a description")
        self.assertEqual(namespace.title, "nothing")
        self.assertEqual(namespace.description, "a description")

    def test_number(self):
        """Test a number argument."""
        args = CommandArgs()
        args.add_argument("number")
        namespace = args.parse("38")
        self.assertEqual(namespace.number, 38)

        # Try an invalid number
        args = CommandArgs()
        number = args.add_argument("number")
        result = args.parse("no")
        self.assertIsInstance(result, ArgumentError)
        self.assertEqual(str(result), number.msg_invalid_number.format(number="no"))

        # Try with an optional number
        args = CommandArgs()
        args.add_argument("number", optional=True, default=1)
        args.add_argument("text")
        namespace = args.parse("2 red apples")
        self.assertEqual(namespace.number, 2)
        self.assertEqual(namespace.text, "red apples")
        namespace = args.parse("red apple")
        self.assertEqual(namespace.number, 1)
        self.assertEqual(namespace.text, "red apple")

        # Try with words and an optional number
        args = CommandArgs()
        args.add_argument("number", dest="left", optional=True, default=1)
        args.add_argument("word")
        args.add_argument("number", dest="right")
        namespace = args.parse("2 times 3")
        self.assertEqual(namespace.left, 2)
        self.assertEqual(namespace.word, "times")
        self.assertEqual(namespace.right, 3)
        namespace = args.parse("neg 5")
        self.assertEqual(namespace.left, 1)
        self.assertEqual(namespace.word, "neg")
        self.assertEqual(namespace.right, 5)
