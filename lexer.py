import sys
import re

# Define your token types. You might have more types than this.
TOKEN_TYPES = [
    ('KEYWORD', r'\b(var|print|if)\b'),
    ('IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ('INTEGER', r'\b\d+\b'),
    ('OPERATOR', r'[\+\-\*/]'),
    ('EQUALS', r'='),
    ('OPEN_PAREN', r'\('),
    ('CLOSE_PAREN', r'\)'),
    ('OPEN_BRACE', r'\{'),  # Add token type for '{'
    ('CLOSE_BRACE', r'\}'),  # Add token type for '}'
    ('NEWLINE', r'\n'),
    ('SKIP', r'[ \t]'),
    ('MISMATCH', r'.')
]

def lex(source_code: str):
    pos = 0
    tokens = []
    while pos < len(source_code):
        match = None
        for token_type, regex in TOKEN_TYPES:
            pattern = re.compile(regex)
            match = pattern.match(source_code, pos)
            if match:
                text = match.group(0)
                if token_type != 'SKIP':
                    token = (token_type, text)
                    tokens.append(token)
                break
        if not match:
            raise ValueError(f'Illegal character: {source_code[pos]}')
        else:
            pos = match.end(0)
    return tokens