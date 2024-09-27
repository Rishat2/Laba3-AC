import re
import sys

from isa import Command, Opcode, Variable, write_code


def is_integer(value: str):
    return value.isdigit()


def is_string(value: str):
    return value.isalpha()


def delete_comment(line: str):
    return re.sub(r";.*", "", line)


def delete_spaces(line: str):
    return re.sub(r"\s+", " ", line.strip())


def clean_code(code: str):
    lines = code.splitlines()
    lines = map(delete_comment, lines)
    lines = map(delete_spaces, lines)
    lines = filter(bool, lines)
    return "\n".join(lines)


def translate_section_data(section_data: str):
    global address
    global variables

    lines = section_data.splitlines()
    link_variables = {}

    for line in lines:
        line = line.split(":", 1)
        name = line[0].strip()
        value = line[1].strip()

        if is_integer(value):
            value = int(value)
            variable = Variable(name, address, [value], False)
            variables[name] = variable
            address += 1
        elif is_string(value):
            chars = [len(value)]
            for char in value:
                chars.append(ord(char))
            variable = Variable(name, address, chars, True)
            variables[name] = variable
            address += len(chars)
        elif value.startswith("bf"):
            size = int(value.split(" ", 1)[1])
            variable = Variable(name, address, [0] * size, False)
            variables[name] = variable
            address += size
        else:
            variable = Variable(name, address, [0], False)
            variables[name] = variable
            link_variables[name] = value
            address += 1

    for link_variable in link_variables:
        variable_name = link_variables[link_variable]
        variables[link_variable].data = [variables[variable_name].address]

    assert address <= 2000, "This program does not fit in memory"


def translate_section_text(section_text: str):
    global address
    global variables

    lines = section_text.splitlines()
    labels = {}
    commands = []

    for line in lines:
        if line.startswith("."):
            labels[line[1:-1]] = address
        else:
            commands.append(line)
            address += 1

    lines = "\n".join(commands).splitlines()
    commands = []

    for line in lines:
        commands.append(translate_command(line, labels))

    return commands


def translate_command(line, labels):
    global variables

    parts = line.split(" ")
    opcode = Opcode.from_string(parts[0])

    if opcode in [Opcode.JMP, Opcode.JZ, Opcode.JNZ, Opcode.CALL]:
        return Command(opcode, labels[parts[1]])
    if opcode == Opcode.LIT:
        if is_integer(parts[1]):
            value = int(parts[1])
        else:
            value = variables[parts[1]].address
        return Command(opcode, value)
    return Command(opcode)


def translate_variables(machine_code):
    global variables

    for variable in variables:
        if variables[variable].name in ["in", "out"]:
            machine_code.append({"value": 0})
            continue
        for char in variables[variable].data:
            machine_code.append({"value": char})
    return machine_code


def translate_commands(commands, machine_code):
    for command in commands:
        if command.operand is None:
            machine_code.append({"opcode": command.opcode, "operand": None})
        else:
            machine_code.append({"opcode": command.opcode, "operand": command.operand})
    return machine_code


def translate(code):
    global address
    global variables

    code = clean_code(code)
    section_data_index = code.find("section .data:")
    section_text_index = code.find("section .text:")
    section_data = code[section_data_index + len("section .data:") + 1 : section_text_index]
    section_text = code[section_text_index + len("section .text:") + 1 :]

    variables = {
        "in": Variable("in", 1, [0], False),
        "out": Variable("out", 2, [0], False),
    }
    address = 3

    translate_section_data(section_data)
    commands_address = address
    commands = translate_section_text(section_text)

    machine_code = [{"value": commands_address}]

    machine_code = translate_variables(machine_code)
    machine_code = translate_commands(commands, machine_code)

    assert address <= 2000, "This program does not fit in memory"

    return machine_code


def main(source, target):
    with open(source, encoding="utf-8") as f:
        source = f.read()

    machine_code = translate(source)
    write_code(target, machine_code)

    print(f"source LoC: {len(source.splitlines())} code instr: {len(machine_code)}")


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Invalid usage: python3 translator.py <source_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
