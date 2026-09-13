import unittest
from pathlib import Path

from IDE.block_editor import AstSourceGenerator
from lexer.lexer import Lexer
from parser.parser import Parser


class BlockEditorConversionTests(unittest.TestCase):
    def test_ast_source_round_trip_preserves_hangullo_structure(self):
        source = Path("examples/04_condition.hg").read_text(encoding="utf-8")
        program = Parser(Lexer(source).tokenize(), source).parse()
        generated = AstSourceGenerator().generate(program)
        reparsed = Parser(Lexer(generated).tokenize(), generated).parse()
        self.assertEqual(len(program.statements), len(reparsed.statements))
        self.assertTrue(generated.endswith("\n"))

    def test_generator_uses_current_parenthesized_syntax(self):
        source = "출력(\"Hello\")\n"
        program = Parser(Lexer(source).tokenize(), source).parse()
        self.assertEqual(AstSourceGenerator().generate(program), source)


if __name__ == "__main__":
    unittest.main()
