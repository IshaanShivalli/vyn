import re
from enum import Enum, auto


class TokenType(Enum):
    KEYWORD    = auto()
    IDENTIFIER = auto()
    INTEGER    = auto()
    FLOAT      = auto()
    STRING     = auto()
    BOOL       = auto()
    NULL       = auto()
    OP         = auto()
    COMMA      = auto()
    LPAREN     = auto()
    RPAREN     = auto()
    SEMICOLON  = auto()
    STAR       = auto()
    DOT        = auto()
    EOF        = auto()


KEYWORDS = {
    'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES',
    'UPDATE', 'SET', 'DELETE', 'CREATE', 'DROP', 'TABLE',
    'INDEX', 'ON', 'ALTER', 'ADD', 'COLUMN', 'RENAME', 'TO',
    'MODIFY', 'UNIQUE', 'PRIMARY', 'KEY', 'NOT', 'NULL',
    'DEFAULT', 'AND', 'OR', 'IN', 'IS', 'LIKE', 'BETWEEN',
    'EXISTS', 'HAVING', 'GROUP', 'BY', 'ORDER', 'ASC', 'DESC',
    'LIMIT', 'OFFSET', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL',
    'OUTER', 'CROSS', 'NATURAL', 'UNION', 'ALL', 'DISTINCT',
    'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'AS', 'TRUE', 'FALSE',
    'BEGIN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'TRANSACTION',
    'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COALESCE', 'NULLIF',
    'CAST', 'DATABASE', 'CONSTRAINT', 'FOREIGN', 'REFERENCES',
    'CHECK', 'RETURNING', 'EXPLAIN', 'TRUNCATE', 'INT', 'FLOAT',
    'TEXT', 'VARCHAR', 'BOOL', 'BLOB',
}

OPS = ['<>', '!=', '>=', '<=', '=', '<', '>', '+', '-', '/', '%', '||']


class Token:
    def __init__(self, ttype, value, pos):
        self.ttype = ttype
        self.value = value
        self.pos   = pos

    def __repr__(self):
        return f"Token({self.ttype.name}, {self.value!r}, pos={self.pos})"


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos    = 0
        self.tokens = []

    def _peek(self, ahead=0):
        p = self.pos + ahead
        return self.source[p] if p < len(self.source) else ''

    def _advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        return ch

    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch in ' \t\r\n':
                self.pos += 1
            elif ch == '-' and self._peek(1) == '-':
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.pos += 1
            elif ch == '/' and self._peek(1) == '*':
                self.pos += 2
                while self.pos < len(self.source):
                    if self.source[self.pos] == '*' and self._peek(1) == '/':
                        self.pos += 2
                        break
                    self.pos += 1
            else:
                break

    def _read_string(self, quote):
        start = self.pos
        self._advance()
        buf = []
        while self.pos < len(self.source):
            ch = self._advance()
            if ch == quote:
                return ''.join(buf)
            if ch == '\\':
                esc = self._advance()
                buf.append({'n': '\n', 't': '\t', 'r': '\r'}.get(esc, esc))
            else:
                buf.append(ch)
        raise LexerError(f"Unterminated string at pos {start}")

    def _read_number(self):
        start = self.pos
        is_float = False
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self.pos += 1
        if self.pos < len(self.source) and self.source[self.pos] == '.':
            is_float = True
            self.pos += 1
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                self.pos += 1
        raw = self.source[start:self.pos]
        return (float(raw), TokenType.FLOAT) if is_float else (int(raw), TokenType.INTEGER)

    def _read_identifier(self):
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
        return self.source[start:self.pos]

    def tokenize(self):
        while True:
            self._skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                self.tokens.append(Token(TokenType.EOF, None, self.pos))
                break
            start = self.pos
            ch = self.source[self.pos]

            if ch in ('"', "'", '`'):
                s = self._read_string(ch)
                self.tokens.append(Token(TokenType.STRING, s, start))
                continue

            if ch.isdigit() or (ch == '-' and self._peek(1).isdigit() and
                                  (not self.tokens or self.tokens[-1].ttype in
                                   (TokenType.OP, TokenType.COMMA, TokenType.LPAREN))):
                if ch == '-':
                    self.pos += 1
                val, ttype = self._read_number()
                if ch == '-':
                    val = -val
                self.tokens.append(Token(ttype, val, start))
                continue

            if ch.isalpha() or ch == '_':
                word = self._read_identifier()
                up = word.upper()
                if up in ('TRUE', 'FALSE'):
                    self.tokens.append(Token(TokenType.BOOL, up == 'TRUE', start))
                elif up == 'NULL':
                    self.tokens.append(Token(TokenType.NULL, None, start))
                elif up in KEYWORDS:
                    self.tokens.append(Token(TokenType.KEYWORD, up, start))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, word, start))
                continue

            matched_op = None
            for op in OPS:
                if self.source[self.pos:self.pos + len(op)] == op:
                    matched_op = op
                    break
            if matched_op:
                self.pos += len(matched_op)
                self.tokens.append(Token(TokenType.OP, matched_op, start))
                continue

            if ch == '*':
                self.pos += 1
                self.tokens.append(Token(TokenType.STAR, '*', start))
                continue
            if ch == ',':
                self.pos += 1
                self.tokens.append(Token(TokenType.COMMA, ',', start))
                continue
            if ch == '(':
                self.pos += 1
                self.tokens.append(Token(TokenType.LPAREN, '(', start))
                continue
            if ch == ')':
                self.pos += 1
                self.tokens.append(Token(TokenType.RPAREN, ')', start))
                continue
            if ch == ';':
                self.pos += 1
                self.tokens.append(Token(TokenType.SEMICOLON, ';', start))
                continue
            if ch == '.':
                self.pos += 1
                self.tokens.append(Token(TokenType.DOT, '.', start))
                continue

            raise LexerError(f"Unexpected character '{ch}' at pos {start}")

        return self.tokens


def tokenize(source):
    return Lexer(source).tokenize()