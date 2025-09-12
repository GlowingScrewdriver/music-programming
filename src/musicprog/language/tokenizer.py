import re

class TokenError (Exception):
    """Raised when a token is invalid"""
    def __init__ (self, word: str, line: int, col: int):
        super ().__init__ (
            f"Line {line}, column {col}: "
            f"Invalid token: {word}"
        )

class Token:
    """Base token class"""
    def __init__ (self, word, line, col):
        self.word = word
        self.line = line
        self.col = col

    def __repr__ (self):
        toktype = self.__class__.__name__
        data = repr (self.word)
        line, col = self.line, self.col
        return f"{toktype}({data}, line={line}, col={col})"

class LIST_START (Token):
    pass
class LIST_END (Token):
    pass
class SVARA_NAME (Token):
    pass
class GAMAKA_NAME (Token):
    pass
class GAMAKA_END (Token):
    pass

Pattern_TokenType = (
    ("{", LIST_START),
    ("}", LIST_END),
    (r",|[a-zA-Z].*", SVARA_NAME),
    (r":.*", GAMAKA_NAME),
)
def make_token (word: str, line: int, col: int) -> Token:
    for pattern, token_ctor in Pattern_TokenType:
        if re.fullmatch (pattern, word):
            return token_ctor (word, line, col)

    # We couldn't match this against a valid pattern
    raise TokenError (word, line, col)

def tokenize (program):
    line, col = 1, 0
    wordl = []
    for char in program:
        col += 1
        if char.isspace ():
            # 1. A whitespace ends a token
            if wordl:
                word = "".join (wordl)
                # Note that `col` is where the token _ends_,
                # not starts
                yield make_token (word, line, col - len (word))
                wordl = []
            if char == "\n":
                # 2. A newline starts... a new line
                line += 1; col = 0
        else:
            # 3. Anything else is part of a token
            wordl.append (char)

if __name__ == "__main__":
    from sys import stdin
    print (*tokenize (stdin.read ()), sep = "\n")
