import tokenizer as t
from typing import Iterable, Self

class ParseError (Exception):
    def __init__ (self, msg, line, col):
        super ().__init__ (
            f"Line {node.line}, column {node.col}: "
            + msg
        )

class Node:
    """Base AST node class"""
    def __init__ (self, line: int, col: int, children: tuple[Self]):
        self.line = line
        self.col = col
        self.children = children

class SVARA (Node):
    @classmethod
    def get (cls, tokens: list[t.Token]):
        tok = tokens.pop (0)
        if not isinstance (tok, t.SVARA_NAME):
            raise ParseError (
                "Expected SVARA_NAME",
                tok.line, tok.col
            )
        res = cls (tok.line, tok.col, children = ())
        res.name = tok.word
        return res

class GAMAKA (Node):
    @classmethod
    def get (cls, tokens: list[t.Token]):
        tok = tokens.pop (0)
        if not isinstance (tok, t.GAMAKA_NAME):
            raise ParseError (
                "Expected GAMAKA_NAME",
                tok.line, tok.col
            )
        res = cls (tok.line, tok.col, children = ())
        res.name = tok.word
        return res

class LIST (Node):
    @classmethod
    def get (cls, tokens: list[t.Token], /, elem_type: type):
        assert issubclass (elem_type, Node)

        tok = tokens.pop (0)
        line, col = tok.line, tok.col
        if not isinstance (tok, t.LIST_START):
            raise ParseError (
                "Expected LIST_START",
                line, col
            )

        elements = []
        while True:
            if isinstance (tokens [0], t.LIST_END):
                break
            elem = elem_type.get (tokens)
            elements.append (elem)

        res = cls (line, col, elements)

class SONG (Node):
    pass

def parse (program: list[t.Token]):
    LIST.get (program, elem_type = SVARA)

if __name__ == "__main__":
    from sys import stdin
    parse ([*t.tokenize (stdin.read ())])
