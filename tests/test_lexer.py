import unittest

from errors import HangulloLexerError
from lexer.lexer import Lexer


class LexerTests(unittest.TestCase):
    def token_types(self, source):
        return [token.type for token in Lexer(source).tokenize()]

    def test_keywords_operators_and_identifiers(self):
        types = self.token_types(
            "출력(한글이름 + english_1 >= 3.14 그리고 참): # 주석\n"
        )
        self.assertEqual(
            types,
            [
                "PRINT", "LPAREN", "IDENTIFIER", "PLUS", "IDENTIFIER",
                "GTE", "NUMBER", "AND", "TRUE", "RPAREN", "COLON",
                "NEWLINE", "EOF",
            ],
        )

    def test_strings_and_escaped_characters(self):
        tokens = Lexer('출력("한글\\n\\t\\"\\\\")').tokenize()
        self.assertEqual(tokens[2].value, '한글\n\t"\\')

    def test_blank_lines_and_missing_final_newline(self):
        tokens = Lexer("\n\n변수 값 = 1").tokenize()
        self.assertEqual(tokens[-1].type, "EOF")
        self.assertEqual([token.type for token in tokens].count("NEWLINE"), 2)

    def test_indentation_increase_and_decrease(self):
        types = self.token_types("만약 참:\n    출력(1)\n출력(2)")
        self.assertIn("INDENT", types)
        self.assertIn("DEDENT", types)

    def test_invalid_indentation_and_character(self):
        with self.assertRaises(HangulloLexerError):
            Lexer("만약 참:\n    출력(1)\n  출력(2)\n").tokenize()
        with self.assertRaises(HangulloLexerError):
            Lexer("출력(@)\n").tokenize()

    def test_comment_and_number_starting_identifier_are_not_accepted_as_identifier(self):
        tokens = Lexer("# comment\n123abc\n").tokenize()
        self.assertEqual(
            [token.type for token in tokens],
            ["NEWLINE", "NUMBER", "IDENTIFIER", "NEWLINE", "EOF"],
        )


if __name__ == "__main__":
    unittest.main()
