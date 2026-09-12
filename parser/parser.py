from lexer.lexer import Token
from errors import HangulloParserError
from parser.nodes import (
    BinaryOpNode,
    FunctionCallNode,
    FunctionNode,
    IdentifierNode,
    IfNode,
    InputNode,
    LiteralNode,
    PrintNode,
    ProgramNode,
    RepeatNode,
    ReturnNode,
    UnaryOpNode,
    VarAssignNode,
)


class Parser:
    """토큰을 AST(Abstract Syntax Tree)로 변환한다."""

    def __init__(self, tokens: list[Token], source: str | None = None):
        self.tokens = tokens
        self.position = 0
        self.source_lines = source.splitlines() if source is not None else []

    def parse(self) -> ProgramNode:
        return ProgramNode(self.parse_block(stop_tokens={"EOF"}))

    def parse_block(self, stop_tokens: set[str]) -> list:
        statements = []
        self.skip_newlines()
        while self.current().type not in stop_tokens:
            statement = self.parse_statement()
            statements.append(statement)
            if not isinstance(statement, (IfNode, RepeatNode, FunctionNode)):
                self.consume_statement_end()
            self.skip_newlines()
        return statements

    def parse_statement(self):
        token = self.current()
        if token.type == "PRINT":
            return self.parse_print()
        if token.type == "VAR":
            return self.parse_var_declaration()
        if token.type == "INPUT":
            return self.parse_input()
        if token.type == "IF":
            return self.parse_if()
        if token.type == "REPEAT":
            return self.parse_repeat()
        if token.type == "FUNCTION":
            return self.parse_function()
        if token.type == "RETURN":
            return self.parse_return()
        if token.type == "IDENTIFIER" and self.peek().type == "EQUAL":
            return self.parse_assignment()
        if token.type == "IDENTIFIER" and self.peek().type == "LPAREN":
            return self.parse_function_call()
        self.error(token, f"알 수 없는 문장입니다: {token.value}")

    def parse_print(self) -> PrintNode:
        self.advance()
        self.consume("LPAREN", "출력 뒤에는 '('가 필요합니다.")
        value = self.parse_expression()
        self.consume("RPAREN", "출력 괄호를 닫아야 합니다.")
        return PrintNode(value)

    def parse_var_declaration(self) -> VarAssignNode:
        self.advance()
        name = self.consume("IDENTIFIER", "변수 이름이 필요합니다.").value
        self.consume("EQUAL", "변수 선언에는 '='가 필요합니다.")
        return VarAssignNode(name, self.parse_expression(), declare=True)

    def parse_assignment(self) -> VarAssignNode:
        name = self.consume("IDENTIFIER", "변수 이름이 필요합니다.").value
        self.consume("EQUAL", "값을 대입하려면 '='가 필요합니다.")
        return VarAssignNode(name, self.parse_expression())

    def parse_input(self) -> InputNode:
        self.advance()
        self.consume("LPAREN", "입력 뒤에는 '('가 필요합니다.")
        name = self.consume("IDENTIFIER", "입력을 저장할 변수 이름이 필요합니다.").value
        prompt = None
        if self.match("COMMA"):
            prompt = self.parse_expression()
        self.consume("RPAREN", "입력 괄호를 닫아야 합니다.")
        return InputNode(name, prompt)

    def parse_if(self) -> IfNode:
        self.advance()
        condition = self.parse_expression()
        then_body = self.parse_indented_body("만약")
        elif_branches = []
        while self.match("ELIF"):
            elif_condition = self.parse_expression()
            elif_body = self.parse_indented_body("아니고만약")
            elif_branches.append((elif_condition, elif_body))
        else_body = []
        if self.match("ELSE"):
            else_body = self.parse_indented_body("아니면")
        return IfNode(condition, then_body, else_body, elif_branches)

    def parse_indented_body(self, block_name: str) -> list:
        self.consume("COLON", f"{block_name} 문 뒤에는 ':'가 필요합니다.")
        self.consume_statement_end()
        self.consume("INDENT", f"{block_name} 문 안에 들여쓴 코드가 필요합니다.")
        body = self.parse_block(stop_tokens={"DEDENT", "EOF"})
        self.consume("DEDENT", f"{block_name} 문 블록의 들여쓰기가 필요합니다.")
        return body

    def parse_repeat(self) -> RepeatNode:
        self.advance()
        count = self.parse_expression()
        return RepeatNode(count, self.parse_indented_body("반복"))

    def parse_function(self) -> FunctionNode:
        self.advance()
        name = self.consume("IDENTIFIER", "함수 이름이 필요합니다.").value
        self.consume("LPAREN", "함수 매개변수를 시작하려면 '('가 필요합니다.")
        parameters = []
        if self.current().type != "RPAREN":
            while True:
                parameters.append(self.consume("IDENTIFIER", "매개변수 이름이 필요합니다.").value)
                if not self.match("COMMA"):
                    break
        self.consume("RPAREN", "함수 매개변수를 닫으려면 ')'가 필요합니다.")
        return FunctionNode(name, parameters, self.parse_indented_body("함수"))

    def parse_return(self) -> ReturnNode:
        self.advance()
        if self.current().type in {"NEWLINE", "DEDENT", "EOF"}:
            self.error(self.current(), "반환할 값이 필요합니다.")
        return ReturnNode(self.parse_expression())

    def parse_function_call(self) -> FunctionCallNode:
        name = self.consume("IDENTIFIER", "함수 이름이 필요합니다.").value
        self.consume("LPAREN", "함수 호출에는 '('가 필요합니다.")
        arguments = []
        if self.current().type != "RPAREN":
            while True:
                arguments.append(self.parse_expression())
                if not self.match("COMMA"):
                    break
        self.consume("RPAREN", "함수 호출의 ')'가 필요합니다.")
        return FunctionCallNode(name, arguments)

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        expr = self.parse_and()
        while self.match("OR"):
            expr = BinaryOpNode(expr, "또는", self.parse_and())
        return expr

    def parse_and(self):
        expr = self.parse_equality()
        while self.match("AND"):
            expr = BinaryOpNode(expr, "그리고", self.parse_equality())
        return expr

    def parse_equality(self):
        expr = self.parse_comparison()
        while self.current().type in {"EQEQ", "NEQ"}:
            operator = self.advance().value
            expr = BinaryOpNode(expr, operator, self.parse_comparison())
        return expr

    def parse_comparison(self):
        expr = self.parse_term()
        while self.current().type in {"GT", "GTE", "LT", "LTE"}:
            operator = self.advance().value
            expr = BinaryOpNode(expr, operator, self.parse_term())
        return expr

    def parse_term(self):
        expr = self.parse_factor()
        while self.current().type in {"PLUS", "MINUS"}:
            operator = self.advance().value
            expr = BinaryOpNode(expr, operator, self.parse_factor())
        return expr

    def parse_factor(self):
        expr = self.parse_unary()
        while self.current().type in {"STAR", "SLASH", "PERCENT"}:
            operator = self.advance().value
            expr = BinaryOpNode(expr, operator, self.parse_unary())
        return expr

    def parse_unary(self):
        if self.current().type in {"MINUS", "NOT"}:
            operator = self.advance().value
            return UnaryOpNode(operator, self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        token = self.current()
        if self.match("NUMBER", "STRING"):
            return LiteralNode(token.value)
        if self.match("TRUE"):
            return LiteralNode(True)
        if self.match("FALSE"):
            return LiteralNode(False)
        if self.current().type == "INPUT":
            return self.parse_input()
        if self.current().type == "IDENTIFIER":
            name = self.advance().value
            if self.match("LPAREN"):
                arguments = []
                if self.current().type != "RPAREN":
                    while True:
                        arguments.append(self.parse_expression())
                        if not self.match("COMMA"):
                            break
                self.consume("RPAREN", "함수 호출에는 ')'가 필요합니다.")
                return FunctionCallNode(name, arguments)
            return IdentifierNode(name)
        if self.match("LPAREN"):
            expr = self.parse_expression()
            self.consume("RPAREN", "괄호를 닫으려면 ')'가 필요합니다.")
            return expr
        self.error(token, "표현식이 필요합니다.")

    def consume_statement_end(self) -> None:
        if self.current().type in {"NEWLINE", "EOF"}:
            self.match("NEWLINE")
            return
        self.error(self.current(), "문장 끝에는 줄바꿈이 필요합니다.")

    def skip_newlines(self) -> None:
        while self.match("NEWLINE"):
            pass

    def current(self) -> Token:
        return self.tokens[self.position]

    def peek(self) -> Token:
        if self.position + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.position + 1]

    def advance(self) -> Token:
        token = self.current()
        self.position += 1
        return token

    def match(self, *token_types: str) -> bool:
        if self.current().type in token_types:
            self.advance()
            return True
        return False

    def consume(self, token_type: str, message: str) -> Token:
        if self.current().type == token_type:
            return self.advance()
        self.error(self.current(), message)

    def error(self, token: Token, message: str):
        source_line = None
        if 1 <= token.line <= len(self.source_lines):
            source_line = self.source_lines[token.line - 1]
        raise HangulloParserError(
            message,
            line=token.line,
            column=token.column,
            source_line=source_line,
        )
