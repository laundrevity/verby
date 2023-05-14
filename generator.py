from tree_parser import VarDeclaration, PrintStatement, BinaryOperation, IfStatement
import platform

def generate_code_x86(node, variables, counter):
    if isinstance(node, VarDeclaration):
        variables[node.name] = node.value.value
        return ""
    elif isinstance(node, PrintStatement):
        counter['print'] += 1
        print_id = counter['print']     # get the current print count
        if isinstance(node.expression, BinaryOperation):
            left = variables[node.expression.left.name]
            right = variables[node.expression.right.name]
            # Note that for division, the above implementation does not handle the remainder, 
            # and it assumes integer division. To support floating-point numbers and arithmetic, 
            # we'll need to extend the language and the code generator accordingly.
            operation = {
                '+': 'add',
                '-': 'sub',
                '*': 'imul',
                '/': 'idiv'
            }[node.expression.operator]
            return f"""
section .data
    result{print_id} dq 0
    format{print_id} db "%d", 10, 0

section .text
    extern printf

print{print_id}:
    sub rsp, 8
    mov rax, {left}
    {operation} rax, {right}
    mov [result{print_id}], rax
    mov rdi, format{print_id}
    mov rsi, [result{print_id}]
    xor rax, rax
    call printf
    xor eax, eax
    add rsp, 8
    ret
"""
        else:
            value = variables[node.expression.name]
            return f"""
section .data
    result dq {value}
    format db "%d", 10, 0

section .text
    global main
    extern printf

main:
    sub rsp, 8
    mov rdi, format
    mov rsi, [result]
    xor rax, rax
    call printf
    xor eax, eax
    add rsp, 8
    ret
"""
    else:
        raise NotImplementedError(f"Code generation not implemented for this node type: {node.__class__}")

def generate_code_arm(node, variables, counter):
    if isinstance(node, VarDeclaration):
        variables[node.name] = node.value.value
        return ""
    elif isinstance(node, PrintStatement):
        counter['print'] += 1
        print_id = counter['print']
        if isinstance(node.expression, BinaryOperation):
            left = variables[node.expression.left.name]
            right = variables[node.expression.right.name]
            operation = {
                '+': 'add',
                '-': 'sub',
                '*': 'mul',
                '/': 'sdiv'
            }[node.expression.operator]
            return f"""
.data
    result{print_id}: .word 0
    format{print_id}: .asciz "%d\\n"

.text
    .globl print{print_id}

print{print_id}:
    push {{lr}}
    mov r0, #{left}
    mov r1, #{right}
    {operation} r0, r0, r1
    str r0, [result{print_id}]
    ldr r0, =format{print_id}
    ldr r1, [result{print_id}]
    bl printf
    pop {{lr}}
    bx lr
"""       
        else:
            value = variables[node.expression.name]
            if f'format{value}' not in print_calls:
                print_calls[f'format{value}'] = f"""
section .data
    format{value} db "%d", 10, 0
"""
            return f"""
section .text
    extern printf

main:
    sub rsp, 8
    mov rdi, format{value}
    mov rsi, {value}
    xor rax, rax
    call printf
    xor eax, eax
    add rsp, 8
    ret
"""
    
    elif isinstance(node, IfStatement):
        # Generate the code for if statement
        # ...
        return f""""""

    else:
        raise NotImplementedError(f"Code generation not implemented for this node type: {node.__class__}")

def generate_assembly_x86(syntax_tree):
    variables = {}
    assembly_code = ""
    counter = {'print': 0}
    print_calls = [] # to store print function calls
    for node in syntax_tree:
        assembly_code += generate_code_x86(node, variables, counter)
        if isinstance(node, PrintStatement):
            print_calls.append(f"call print{counter['print']}")

    print_line = '\n '.join(print_calls)
    main_function = f"""
section .text
    global main
    extern printf

main:
    sub rsp, 8
    {print_line}
    xor eax, eax
    add rsp, 8
    ret
"""

    return main_function + assembly_code

def generate_assembly_arm(syntax_tree):
    variables = {}
    assembly_code = ""
    counter = {'print': 0}
    print_calls = []
    for node in syntax_tree:
        assembly_code += generate_code_arm(node, variables, counter)
        if isinstance(node, PrintStatement):
            print_calls.append(f"bl print{counter['print']}")

    print_line = '\n '.join(print_calls)
    main_function = f"""
.text
    .globl main

main:
    push {{lr}}
    {print_line}
    pop {{lr}}
    bx lr
"""

    return main_function + assembly_code

def generate_assembly(syntax_tree):
    architecture = platform.machine()
    if architecture == "x86_64":
        print("x86 detected")
        return generate_assembly_x86(syntax_tree)
    elif architecture.startswith("arm") or architecture.startswith("aarch"):
        print("arm detected")
        return generate_assembly_arm(syntax_tree)
    else:
        raise NotImplementedError(f"Code generation not implemented for this architecture: {architecture}")