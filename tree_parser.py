from lexer import lex

class Node:
    pass

class VarDeclaration(Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class PrintStatement(Node):
    def __init__(self, expression):
        self.expression = expression

class BinaryOperation(Node):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class Identifier(Node):
    def __init__(self, name):
        self.name = name

class Integer(Node):
    def __init__(self, value):
        self.value = value

class IfStatement(Node):
    def __init__(self, condition: BinaryOperation, body: list):
        self.condition = condition
        self.body = body

class SyntaxError(Exception):
    pass

def parse(tokens):
    tokens = list(tokens)
    statements = []

    def parse_statements(body_tokens):
        nonlocal tokens
        tokens = body_tokens
        body = []
        while tokens:
            token_type, _ = tokens[0]
            
            if token_type == "OPEN_BRACE":
                tokens.pop(0)
                body_statements = parse_statements(tokens)
                body.extend(body_statements)
            elif token_type == "CLOSE_BRACE":
                tokens.pop(0)
                break
            elif token_type == "KEYWORD":
                value = tokens[0][1]
                if value == "var":
                    parse_var_declaration()
                elif value == "print":
                    parse_print_statement()
                elif value == "if":
                    parse_if_statement()

            body.append(statements[-1])

        return body

    def parse_var_declaration():
        token_type = tokens[0][0]
        value = tokens[0][1]
        if token_type == 'KEYWORD' and value == 'var':
            _, name = tokens.pop(0)
            _, _ = tokens.pop(0)
            _, value = tokens.pop(0)
            node = VarDeclaration(name, Integer(value))
            statements.append(node)

    def parse_print_statement():
        _, name = tokens.pop(0)
        if tokens and tokens[0][1] in ['+', '-', '*', '/']:
            _, operator = tokens.pop(0)
            _, right_value = tokens.pop(0)
            node = PrintStatement(BinaryOperation(Identifier(name), operator, Identifier(right_value)))
        else:
            node = PrintStatement(Identifier(name))
        statements.append(node)

    def parse_if_statement():
        _, _ = tokens.pop(0)  # Remove 'if' token
        _, _ = tokens.pop(0)  # Remove '(' token
        left_identifier, _ = tokens.pop(0)  # Get left identifier
        operator, _ = tokens.pop(0)  # Get operator
        right_identifier, _ = tokens.pop(0)  # Get right identifier
        _, _ = tokens.pop(0)  # Remove ')' token

        condition = BinaryOperation(
            Identifier(left_identifier), operator, Identifier(right_identifier)
        )

        # Parsing body of if statement
        body = parse_statements(tokens)

        node = IfStatement(condition, body)
        statements.append(node)

    while tokens:
        token_type, _ = tokens[0]

        if token_type == "OPEN_BRACE":
            tokens.pop(0)
            body_statements = parse_statements(tokens)
            statements.extend(body_statements)
        else:
            parse_var_declaration()
            parse_print_statement()
            parse_if_statement()

    return statements