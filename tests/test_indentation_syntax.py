import unittest

from lexer.lexer import Lexer
from parser.parser import Parser


class IndentationSyntaxTests(unittest.TestCase):
    def test_blocks_use_colons_and_indentation(self):
        source = """변수 횟수 = 2
반복 횟수:
    출력 횟수
만약 참:
    출력 "참"
아니면:
    출력 "거짓"
"""

        tokens = Lexer(source).tokenize()

        self.assertNotIn("END", [token.type for token in tokens])
        self.assertEqual(
            [token.type for token in tokens].count("INDENT"),
            3,
        )
        Parser(tokens).parse()

    def test_block_requires_indentation(self):
        source = "만약 참:\n출력 \"실패\"\n"

        with self.assertRaises(SyntaxError):
            Parser(Lexer(source).tokenize()).parse()


if __name__ == "__main__":
    unittest.main()