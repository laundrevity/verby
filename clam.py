import sys
import subprocess
import os
import datetime
import platform
from lexer import lex
from tree_parser import parse
from generator import generate_assembly
import tiktoken
import traceback
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

def print_line_with_token_count(line, current_tokens):
    token_count_string = f"[{current_tokens}/8192]"
    print(f"{token_count_string:>12} | {line}")

def get_file_content(file_path: str):
    with open(file_path, 'r') as f:
        return f.read()

def write_state_file(build_successful: bool, output_messages: str, command: str):
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    build_status = "successful" if build_successful else "failed"

    uname_output = subprocess.run(['uname', '-a'], capture_output=True, text=True).stdout.strip()

    state_content = ""

    for file_name in os.listdir('.'):
        if file_name.endswith('.py') or file_name.endswith('.clam'):
            state_content += f"--- {file_name} ---\n"
            state_content += get_file_content(file_name)
            state_content += "\n\n"

    state_content += f"Extra information:\n"
    state_content += f"Output of 'uname -a': {uname_output}\n"
    state_content += f"Current datetime: {current_datetime}\n\n"

    state_content += f"Command used: {command}\n\n"

    state_content += f"Build status: {build_status}\n"
    state_content += f"Build datetime: {current_datetime}\n\n"
    state_content += f"Output messages:\n{output_messages}\n\n"

    with open("state.txt", "w") as f:
        f.write(state_content)

def compile_clam_file(input_file: str, output_file: str, command: str):
    try:
        with open(input_file, 'r') as f:
            source_code = f.read()

        tokens = lex(source_code)
        syntax_tree = parse(tokens)
        assembly_code = generate_assembly(syntax_tree)

        assembly_file = input_file.replace('.clam', '.s')
        with open(assembly_file, 'w') as f:
            f.write(assembly_code)

        obj_file = input_file.replace('.clam', '.o')

        assembler = "gcc" if platform.machine().startswith("arm") or platform.machine().startswith("aarch") else "nasm"

        if assembler == "gcc":
            assembler_flags = "-x assembler -c"
        elif assembler == "nasm":
            assembler_flags = "-f elf64"
        else:
            raise NotImplementedError(f"Unsupported assembler: {assembler}")

        print(f"using assembler {assembler} with flags: {assembler_flags}")

        assembler_process = subprocess.run([assembler] + assembler_flags.split() + [assembly_file, '-o', obj_file], capture_output=True, text=True)
        linker_process = subprocess.run(['gcc', '-no-pie', obj_file, '-o', output_file], capture_output=True, text=True)
        output_messages = f"arm detected\nusing assembler {assembler}\n"
        output_messages += f"assembler output:\n{assembler_process.stdout}\assembler error:\n{assembler_process.stderr}\n"
        output_messages += f"linker output:\n{linker_process.stdout}\nlinker error:\n{linker_process.stderr}\n"

        build_successful = assembler_process.returncode == 0 and linker_process.returncode == 0
        if build_successful:
            # Execute the binary and capture its output
            execution_process = subprocess.run(['./' + output_file], capture_output=True, text=True)
            output_messages += f"Execution:\n./{output_file}\n{execution_process.stdout}\n{execution_process.stderr}\n"

        write_state_file(build_successful, output_messages, command)
    except SyntaxError as se:
        print(f"Syntax Error: {se}")
        formatted_traceback = traceback.format_exc()
        write_state_file(False, f"Traceback:\n{formatted_traceback}", command)
    except Exception as e:
        print(f"Error: {e}")
        formatted_traceback = traceback.format_exc()
        write_state_file(False, f"Traceback:\n{formatted_traceback}", command)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: python clam_compiler.py <input_file.clam> <output_binary> [--send]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    prompt_gpt4 = None
    send_gpt4 = False

    if len(sys.argv) >= 4:
        send_gpt4 = True

    command = " ".join(sys.argv)
    compile_clam_file(input_file, output_file, command)

    if send_gpt4:
        prompt = open('prompt.txt').read() + "\nSuggest a file to modify, and show the fixed version of the file.\n"
        state = open('state.txt').read()
        messages = [
                {
                    'role': 'system',
                    'content': state
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]

        print(f'sending with prompt: {prompt}...')
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=messages,
            stream=True
        )

        answer = ''
        timestamp = datetime.datetime.now().strftime('%H_%M_%S')
        response_filename = f"response_{timestamp}.md"
        enc = tiktoken.get_encoding("cl100k_base")
        num_setup_tokens = len(enc.encode(prompt)) + len(enc.encode(state))
        
        with open(response_filename, "w") as response_file:
            for chunk in response:
                try:
                    s = chunk['choices'][0]['delta']['content']
                    
                    answer += s
                    lines = s.split('\n')
                    for line in lines[:-1]:
                        num_tokens = len(enc.encode(answer))
                        print_line_with_token_count(line, num_tokens + num_setup_tokens)
                        response_file.write(line + '\n')

                    response_file.write(lines[-1])
                    response_file.flush()  # ensure content is written to file immediately
                except:
                    pass

        
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(answer)
        print(f"Response contained {len(tokens)} tokens")

        for chunk in response:
            try:
                s = chunk['choices'][0]['delta']['content']
                print(s, end='')
                answer += s
            except:
                pass
