from enum import Enum, auto
from typing import List

keywords = {
    "SELECT", "DISTINCT", "JOIN", "WHERE",
    "GROUP", "BY", "HAVING", "OFFSET", "AS",
    "FROM", "LIMIT", "ORDER", "BY", "COUNT", "SUM",

}

operators = {
    '*'
}

punctuation = {
    ';', '(', ')', '{', '}'
}

digits = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}

alphanum = {
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w',
    'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
    'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_'
}


class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    INTEGER_LITERAL = auto()
    STRING_LITERAL = auto()
    EOF = auto()
    OPERATOR = auto()
    PUNCTUATION = auto()


class Token:
    def __init__(self, type, value):
        self.type: TokenType = type
        self.value = value

    def __str__(self):
        return "Token({}:{})".format(self.type.name, self.value)

    def __repr__(self):
        return str(self)


EOF_TOKEN = Token(TokenType.EOF, '')


def isidentifier(c):
    return ('a' <= c <= 'z') or ('A' <= c <= 'Z') or c == '_' or ('0' <= c <= '9')


def tokenize(statement) -> List[Token]:
    pos = 0
    length = len(statement)
    tokens = []
    while pos < length:
        c = statement[pos]
        if c == ' ' or c == '\n':
            pos += 1
        elif c.isdigit():
            value = ''
            while c.isdigit() and pos < length:
                value += c
                pos += 1
                c = statement[pos]

            tokens.append(
                Token(TokenType.INTEGER_LITERAL, value)
            )
        elif ('a' <= c <= 'z') or ('A' <= c <= 'Z') or c == '_':
            value = ''
            while isidentifier(c) and pos < length:
                value += c
                pos += 1
                c = statement[pos]

            if value.upper() in keywords:
                tokens.append(
                    Token(TokenType.KEYWORD, value)
                )
            else:
                tokens.append(
                    Token(TokenType.IDENTIFIER, value)
                )
        elif c in operators:
            tokens.append(
                Token(TokenType.OPERATOR, c)
            )
            pos += 1
        elif c in punctuation:
            tokens.append(
                Token(TokenType.PUNCTUATION, c)
            )
            pos += 1
        else:
            raise ValueError("unrecognized character: {}".format(c))

    print(tokens)
    return tokens


def expect():
    pass
