from dataclasses import dataclass
from errors import HangulloLexerError

@dataclass
class Token:
    type: str
    value: object
    line: int = 0
    column: int = 0


class Lexer:
    """Hangullo 소스 코드를 토큰으로 분해한다."""

    KEYWORDS = {
        "출력": "PRINT",
        "변수": "VAR",
        "입력": "INPUT",
        "만약": "IF",
        "아니면": "ELSE",
        "아니고만약": "ELIF",
        "반복": "REPEAT",
        "함수": "FUNCTION",
        "반환": "RETURN",
        "참": "TRUE",
        "거짓": "FALSE",
        "그리고": "AND",
        "또는": "OR",
        "아니다": "NOT"
    }

    SINGLE_CHAR_TOKENS = {
        "+": "PLUS",
        "-": "MINUS",
        "*": "STAR",
        "/": "SLASH",
        "%": "PERCENT",
        "(": "LPAREN",
        ")": "RPAREN",
        ",": "COMMA",
        "=": "EQUAL",
        ":": "COLON",
        "<": "LT",
        ">": "GT",
    }

    TWO_CHAR_TOKENS = {
        "==": "EQEQ",
        "!=": "NEQ",
        "<=": "LTE",
        ">=": "GTE",
    }

    def __init__(self, source: str):
        self.source = source
        self.tokens: list[Token] = []
        self.position = 0
        self.line = 1
        self.column = 1
        self.indent_stack = [0]
        self.line_start = True

    def tokenize(self) -> list[Token]:
        while not self._is_at_end():
            if self.line_start:
                self._read_indentation()
                if self._is_at_end():
                    break

            char = self._peek()

            if char in " \t\r":
                self._advance()
                continue

            if char == "\n":
                self._add_token("NEWLINE", "\n")
                self._advance_line()
                continue

            if char == "#":
                self._skip_comment()
                continue

            if char == "/" and self._peek_next() == "/":
                self._skip_comment()
                continue

            if char == '"':
                self.line_start = False
                self._read_string()
                continue

            if char.isdigit():
                self.line_start = False
                self._read_number()
                continue

            if self._is_identifier_start(char):
                self.line_start = False
                self._read_identifier()
                continue

            two_chars = char + self._peek_next()
            if two_chars in self.TWO_CHAR_TOKENS:
                self.line_start = False
                self._add_token(self.TWO_CHAR_TOKENS[two_chars], two_chars)
                self._advance()
                self._advance()
                continue

            if char in self.SINGLE_CHAR_TOKENS:
                self.line_start = False
                self._add_token(self.SINGLE_CHAR_TOKENS[char], char)
                self._advance()
                continue

            raise HangulloLexerError(
                f"알 수 없는 문자입니다: {char}",
                line=self.line,
                column=self.column,
                source_line=self.source.splitlines()[self.line - 1]
                if self.line <= len(self.source.splitlines())
                else None,
            )

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token("DEDENT", "", self.line, self.column))
        self.tokens.append(Token("EOF", "", self.line, self.column))
        return self.tokens

    def _read_indentation(self) -> None:
        level = 0
        while self._peek() in " \t":
            level += 4 if self._peek() == "\t" else 1
            self._advance()

        if self._peek() in {"\n", "#"} or self._is_at_end():
            return

        self.line_start = False
        current = self.indent_stack[-1]
        if level > current:
            self.indent_stack.append(level)
            self.tokens.append(Token("INDENT", level, self.line, 1))
        elif level < current:
            while len(self.indent_stack) > 1 and level < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.tokens.append(Token("DEDENT", level, self.line, 1))
            if level != self.indent_stack[-1]:
                raise HangulloLexerError(
                    "들여쓰기 깊이가 일치하지 않습니다.",
                    line=self.line,
                    column=1,
                )

    def _read_string(self) -> None:
        start_line = self.line
        start_column = self.column
        self._advance()
        value = []

        while not self._is_at_end() and self._peek() != '"':
            char = self._advance()
            if char == "\\":
                if self._is_at_end():
                    raise HangulloLexerError(
                        "문자열이 끝나지 않았습니다.",
                        line=start_line,
                        column=start_column,
                        source_line=self.source.splitlines()[start_line - 1]
                        if start_line <= len(self.source.splitlines())
                        else None,
                    )
                escaped = self._advance()
                value.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(escaped, escaped))
            elif char == "\n":
                raise HangulloLexerError(
                    "문자열은 한 줄 안에서 닫아야 합니다.",
                    line=start_line,
                    column=start_column,
                    source_line=self.source.splitlines()[start_line - 1]
                    if start_line <= len(self.source.splitlines())
                    else None,
                )
            else:
                value.append(char)

        if self._is_at_end():
            raise HangulloLexerError(
                "문자열이 끝나지 않았습니다.",
                line=start_line,
                column=start_column,
                source_line=self.source.splitlines()[start_line - 1]
                if start_line <= len(self.source.splitlines())
                else None,
            )

        self._advance()
        self.tokens.append(Token("STRING", "".join(value), start_line, start_column))

    def _read_number(self) -> None:
        start = self.position
        line = self.line
        column = self.column

        while self._peek().isdigit():
            self._advance()

        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()

        text = self.source[start:self.position]
        value = float(text) if "." in text else int(text)
        self.tokens.append(Token("NUMBER", value, line, column))

    def _read_identifier(self) -> None:
        start = self.position
        line = self.line
        column = self.column

        while self._is_identifier_part(self._peek()):
            self._advance()

        text = self.source[start:self.position]
        token_type = self.KEYWORDS.get(text, "IDENTIFIER")
        self.tokens.append(Token(token_type, text, line, column))

    def _skip_comment(self) -> None:
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _add_token(self, token_type: str, value: object) -> None:
        self.tokens.append(Token(token_type, value, self.line, self.column))

    def _advance(self) -> str:
        char = self.source[self.position]
        self.position += 1
        self.column += 1
        return char

    def _advance_line(self) -> None:
        self.position += 1
        self.line += 1
        self.column = 1
        self.line_start = True

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.position]

    def _peek_next(self) -> str:
        if self.position + 1 >= len(self.source):
            return "\0"
        return self.source[self.position + 1]

    def _is_at_end(self) -> bool:
        return self.position >= len(self.source)

    @staticmethod
    def _is_identifier_start(char: str) -> bool:
        return char == "_" or char.isalpha()

    @staticmethod
    def _is_identifier_part(char: str) -> bool:
        return char == "_" or char.isalpha() or char.isdigit()
