import json
from enum import Enum as Enum


class Opcode(str, Enum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    INC = "inc"
    DEC = "dec"
    DUP = "dup"
    OVER = "over"
    SWITCH = "switch"
    CMP = "cmp"
    JMP = "jmp"
    JZ = "jz"
    JNZ = "jnz"
    CALL = "call"
    RET = "ret"
    LIT = "lit"
    PUSH = "push"
    POP = "pop"
    DROP = "drop"
    HALT = "halt"

    def __init__(self, mnemonic):
        self.mnemonic = mnemonic

    @classmethod
    def from_string(cls, value):
        for opcode in cls:
            if opcode.mnemonic == value:
                return opcode
        return None


class Variable:
    def __init__(self, name, address, data, is_string):
        self.name = name
        self.address = address
        self.data = data
        self.is_string = is_string


class Command:
    def __init__(self, opcode: Opcode, operand=None):
        self.opcode = opcode
        self.operand = operand


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[\n" + ",\n ".join(buf) + "\n]")


def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        if "opcode" in instr:
            instr["opcode"] = Opcode(instr["opcode"])

    return code
