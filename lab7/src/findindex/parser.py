from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class TermNode:
    term: str


@dataclass
class PhraseNode:
    phrase: str


@dataclass
class NotNode:
    operand: 'Node'


@dataclass
class AndNode:
    left: 'Node'
    right: 'Node'


@dataclass
class OrNode:
    left: 'Node'
    right: 'Node'


Node = Union[TermNode, PhraseNode, NotNode, AndNode, OrNode]


class Lexer:
    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.current_char: Optional[str] = self.text[0] if self.text else None

    def advance(self) -> None:
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def get_tokens(self) -> List[str]:
        tokens: List[str] = []
        while self.current_char is not None:
            if self.current_char.isspace():
                self.advance()
            elif self.current_char in '()':
                tokens.append(self.current_char)
                self.advance()
            elif self.current_char == '"':
                tokens.append(self.read_phrase())
            else:
                tokens.append(self.read_term())
        return tokens

    def read_phrase(self) -> str:
        result = '"'
        self.advance()
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        result += '"'
        self.advance()
        return result

    def read_term(self) -> str:
        result = ''
        while self.current_char is not None and not self.current_char.isspace() and self.current_char not in '()"':
            result += self.current_char
            self.advance()
        return result


class Parser:
    def __init__(self, tokens: List[str]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.current_token: Optional[str] = self.tokens[0] if self.tokens else None

    def advance(self) -> None:
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def parse(self) -> Optional[Node]:
        if not self.tokens:
            return None
        return self.parse_or()

    def parse_or(self) -> Node:
        node = self.parse_and()
        while self.current_token and self.current_token.upper() in ('OR', '|'):
            self.advance()
            right = self.parse_and()
            node = OrNode(left=node, right=right)
        return node

    def parse_and(self) -> Node:
        node = self.parse_not()
        while self.current_token and (self.current_token.upper() in ('AND', '&&') or (
                self.current_token not in (')', 'OR', '|') and not self.current_token.upper().startswith(
                'NOT') and self.current_token != '!')):
            if self.current_token.upper() in ('AND', '&&'):
                self.advance()
            right = self.parse_not()
            node = AndNode(left=node, right=right)
        return node

    def parse_not(self) -> Node:
        if self.current_token and (self.current_token.upper() == 'NOT' or self.current_token == '!'):
            self.advance()
            operand = self.parse_not()
            return NotNode(operand=operand)
        return self.parse_primary()

    def parse_primary(self) -> Node:
        if self.current_token is None:
            raise SyntaxError("Unexpected end of query")

        if self.current_token == '(':
            self.advance()
            node = self.parse_or()
            if self.current_token == '(':  # type: ignore
                raise SyntaxError("Expected closing parenthesis")
            self.advance()
            return node

        if self.current_token.startswith('"') and self.current_token.endswith('"'):
            phrase = self.current_token[1:-1]
            self.advance()
            return PhraseNode(phrase=phrase)

        term = self.current_token
        self.advance()
        return TermNode(term=term)


def parse_query(query: str) -> Optional[Node]:
    lexer = Lexer(query)
    tokens = lexer.get_tokens()
    parser = Parser(tokens)
    return parser.parse()