from . import tokenizer as t
from typing import Iterable, Self

class ParseError (Exception):
    def __init__ (self, msg, line, col):
        super ().__init__ (
            f"Line {line}, column {col}: "
            + msg
        )

class Node:
    """Base AST node class"""
    def __init__ (
        self, line: int, col: int,
        children: tuple[Self, ...], name: str | None = None
    ):
        self.line = line
        self.col = col
        self.children = children
        self.name = name

    @classmethod
    def get (cls, tokens: list[t.Token]):
        """Parse a node of this type"""
        raise NotImplementedError ()

class SVARA (Node):
    @classmethod
    def get (cls, tokens: list[t.Token]):
        # Get the svara name
        tok = tokens.pop (0)
        if not isinstance (tok, t.SVARA_NAME):
            raise ParseError (
                "Expected SVARA_NAME",
                tok.line, tok.col
            )
        name = tok.word
        # Count the following commas
        duration = 1
        while isinstance (tokens [0], t.GAP):
            tokens.pop (0)
            duration += 1

        return cls (
            tok.line, tok.col,
            children = (duration,), name = tok.word
        )

    def get_duration (self) -> int:
        return self.children [0]

class GAMAKA (Node):
    @classmethod
    def get (cls, tokens: list[t.Token]):
        # Get the gamaka name
        tok = tokens.pop (0)
        if not isinstance (tok, t.GAMAKA_NAME):
            raise ParseError (
                "Expected GAMAKA_NAME",
                tok.line, tok.col
            )
        gamaka_name = tok.word

        # Get the following svaras
        svaras = []
        while isinstance (tokens [0], t.SVARA_NAME):
            svaras.append (SVARA.get (tokens))

        return cls (
            tok.line, tok.col,
            children = tuple (svaras), name = gamaka_name
        )

class LINE (Node):
    @classmethod
    def get (cls, tokens: list[t.Token]):
        line, col = tokens [0].line, tokens [0].col
        # Get the list of svaras
        svaras = LIST.get_of_type (tokens, elem_type = SVARA)
        # Get the list of gamakas
        gamakas = LIST.get_of_type (tokens, elem_type = GAMAKA)

        slen, glen = svaras.length (), gamakas.length ()
        if slen != glen:
            raise ParseError (
                f"Expected equal numbers of SVARAs and GAMAKAs, "
                f"got {slen} SVARAs and {glen} GAMAKAs",
                line, col
            )
        return cls (
            line, col,
            children = (svaras.children, gamakas.children)
        )

    def get_svaras (self) -> Iterable[SVARA]:
        return self.children [0]

    def get_gamakas (self) -> Iterable[SVARA]:
        return self.children [1]

class LIST (Node):
    @classmethod
    def get_of_type (cls, tokens: list[t.Token], /, elem_type: type):
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
                tokens.pop (0)
                break
            elem = elem_type.get (tokens)
            elements.append (elem)

        return cls (line, col, children = tuple (elements))

    @classmethod
    def get_empty (cls, tokens: list[t.Token]):
        line, col = tokens [0].line, tokens [0].col
        return cls (line, col, children = ())

    @classmethod
    def get (* _args):
        raise NotImplementedError (
            "Please use `LIST.get_of_type` or `LIST.get_empty` instead"
        )

    def length (self):
        return len (self.children)

class SONG (Node):
    @classmethod
    def get (cls, tokens: list[t.Token]):
        line, col = tokens [0].line, tokens [0].col
        lines = LIST.get_of_type (tokens, elem_type = LINE)
        return cls (line, col, children = lines.children)

    def get_svaras (self) -> Iterable[SVARA]:
        for line in self.children:
            yield from line.get_svaras ()

    def get_gamakas (self) -> Iterable[GAMAKA]:
        for line in self.children:
            yield from line.get_gamakas ()

def parse (program: list[t.Token]):
    return SONG.get (program)

if __name__ == "__main__":
    from sys import stdin
    parse ([*t.tokenize (stdin.read ())])
