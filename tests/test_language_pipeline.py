import builtins
import io
import unittest
from contextlib import redirect_stdout

from compiler.codegen.python import PythonCodeGenerator
from errors import HangulloCompilerError, HangulloParserError
from lexer.lexer import Lexer
from parser.nodes import IfNode, ReturnNode
from parser.parser import Parser


class LanguagePipelineTests(unittest.TestCase):
    def parse(self, source):
        return Parser(Lexer(source).tokenize(), source).parse()

    def generate(self, source):
        return PythonCodeGenerator().generate(self.parse(source))

    def test_elif_and_return_generate_and_execute(self):
        source = """변수 점수 = 85
만약 점수 >= 90:
    출력("A")
아니고만약 점수 >= 80:
    출력("B")
아니면:
    출력("C")
함수 더하기(가, 나):
    반환 가 + 나
변수 결과 = 더하기(3, 5)
출력(결과)
"""
        code = self.generate(source)
        self.assertIn("elif", code)
        self.assertIn("return", code)
        output = io.StringIO()
        with redirect_stdout(output):
            exec(code, {"__builtins__": builtins.__dict__})
        self.assertEqual(output.getvalue().splitlines(), ["B", "8"])

    def test_nested_repeat_and_expression_precedence(self):
        source = """반복 3:
    출력(2 + 3 * 4)
    출력((2 + 3) * 4)
    출력(참 그리고 거짓)
"""
        output = io.StringIO()
        with redirect_stdout(output):
            exec(self.generate(source), {"__builtins__": builtins.__dict__})
        self.assertEqual(output.getvalue().splitlines(), ["14", "20", "False"] * 3)

    def test_input_can_be_used_as_assignment_expression(self):
        source = '변수 이름 = 입력(이름, "이름: ")\n출력(이름)\n'
        code = self.generate(source)
        namespace = {"__builtins__": {**builtins.__dict__, "input": lambda prompt: "민수"}}
        output = io.StringIO()
        with redirect_stdout(output):
            exec(code, namespace)
        self.assertEqual(output.getvalue(), "민수\n")

    def test_parser_errors_are_hangullo_errors(self):
        with self.assertRaises(HangulloParserError):
            self.parse("출력 \"괄호 없음\"\n")
        with self.assertRaises(HangulloParserError):
            self.parse("알수없는문장\n")

    def test_return_outside_function_is_compiler_error(self):
        with self.assertRaises(HangulloCompilerError):
            self.generate("반환 1\n")


if __name__ == "__main__":
    unittest.main()
