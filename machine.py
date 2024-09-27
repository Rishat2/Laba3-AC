from __future__ import annotations

import logging
import sys
from typing import ClassVar

from isa import Opcode, read_code


def alu_add(value1, value2):
    return value1 + value2


def alu_sub(value1, value2):
    return value1 - value2


def alu_mul(value1, value2):
    return value1 * value2


def alu_div(value1, value2):
    return value1 / value2


def alu_mod(value1, value2):
    return value1 % value2


def alu_cmp(value1, value2):
    return value1 - value2


def alu_inc(value):
    return value + 1


def alu_dec(value):
    return value - 1


class Alu:
    operations: ClassVar[list[Opcode]] = [
        Opcode.ADD,
        Opcode.SUB,
        Opcode.MUL,
        Opcode.DIV,
        Opcode.MOD,
        Opcode.CMP,
        Opcode.INC,
        Opcode.DEC,
    ]
    z_flag = None

    def __init__(self):
        self.z_flag = 0

    # flake8: noqa: C901
    def compute(self, value1, value2, opcode):
        assert opcode in self.operations, f"Unknown ALU command {opcode.mnemonic}"
        if opcode == Opcode.ADD:
            value = alu_add(value1, value2)
        elif opcode == Opcode.SUB:
            value = alu_sub(value1, value2)
        elif opcode == Opcode.MUL:
            value = alu_mul(value1, value2)
        elif opcode == Opcode.DIV:
            value = alu_div(value1, value2)
        elif opcode == Opcode.MOD:
            value = alu_mod(value1, value2)
        elif opcode == Opcode.CMP:
            value = alu_cmp(value1, value2)
        elif opcode == Opcode.INC:
            value = alu_inc(value1)
        else:
            value = alu_dec(value1)
        self.set_flags(value)
        return value

    def set_flags(self, value):
        if value == 0:
            self.z_flag = True
        else:
            self.z_flag = False


class DataPath:
    data_stack = None

    data_stack_top1 = None

    data_stack_top2 = None

    data_stack_size = None

    address_stack = None

    address_stack_top = None

    address_stack_size = None

    pc = None

    memory = None

    memory_size = None

    alu: Alu = None

    input_buffer = None

    output_buffer = None

    def __init__(self, machine_code, input_tokens):
        self.data_stack = []
        self.data_stack_top1 = 0
        self.data_stack_top2 = 0
        self.data_stack_size = 1024

        self.address_stack = []
        self.address_stack_top = 0
        self.address_stack_size = 1024

        self.pc = 0

        self.memory = [0] * 2048
        for i in range(len(machine_code)):
            self.memory[i] = machine_code[i]
        self.memory_size = 2048

        self.alu = Alu()
        self.input_buffer: list = input_tokens
        self.output_buffer = []

    def signal_write_data_stack(self, value):
        assert len(self.data_stack) + 1 < self.data_stack_size, "Stack of data overflowed"
        self.data_stack.append(value)

    def signal_latch_data_stack_top1(self, value):
        self.data_stack_top1 = value

    def signal_latch_data_stack_top2(self, value):
        self.data_stack_top2 = value

    def signal_read_data_stack(self):
        assert len(self.data_stack) != 0, "Stack of data is empty"
        return self.data_stack.pop()

    def signal_latch_address_stack_top(self, value):
        self.address_stack_top = value

    def signal_read_address_stack(self):
        assert len(self.address_stack) != 0, "Stack of addresses is empty"
        return self.address_stack.pop()

    def signal_write_address_stack(self, value):
        assert len(self.address_stack) + 1 < self.address_stack_size, "Stack of addresses overflowed"
        self.address_stack.append(value)

    def signal_latch_pc(self, value):
        self.pc = value

    def signal_write_memory(self, address, value):
        assert address != 1, "Address = input_address"
        if address == 2:
            char = chr(value)
            logging.debug("output: %s << %s", repr("".join(self.output_buffer)), repr(char))
            self.output_buffer.append(char)
        else:
            assert address < self.memory_size, f"Memory doesn't contain address {address}"
            self.memory[address] = {"value": value}

    def signal_read_memory(self, address):
        if address == 1:
            assert len(self.input_buffer) > 0, "Input buffer is empty"
            char = ord(self.input_buffer.pop())
            logging.debug("input: %s", repr(chr(char)))
            return char
        assert address < self.memory_size, f"Memory doesn't contain address {address}"
        if "value" in self.memory[address]:
            return self.memory[address]["value"]
        return self.memory[address]


class ControlUnit:
    tick_counter = None

    data_path: DataPath = None

    current_instruction = None

    current_operand = None

    def __init__(self, data_path: DataPath):
        self.tick_counter = 0
        self.data_path = data_path

    def tick(self):
        self.tick_counter += 1

    def initialization(self):
        first_address = self.data_path.signal_read_memory(self.data_path.pc)
        self.data_path.signal_latch_data_stack_top1(first_address)
        self.tick()

        self.data_path.signal_latch_pc(self.data_path.data_stack_top1)
        self.tick()

    def decode_and_execute_control_flow_instruction(self, opcode, operand):
        if opcode == Opcode.JMP:
            return self.execute_jmp(operand)
        if opcode == Opcode.JZ:
            return self.execute_jz(operand)
        if opcode == Opcode.JNZ:
            return self.execute_jnz(operand)
        if opcode == Opcode.CALL:
            return self.execute_call(operand)
        if opcode == Opcode.RET:
            return self.execute_ret()
        if opcode == Opcode.HALT:
            self.execute_halt()
        return False

    def execute_jmp(self, address):
        self.data_path.signal_latch_data_stack_top1(address)
        self.tick()

        self.data_path.pc = self.data_path.data_stack_top1
        self.tick()

        logging.debug("%s", self.__repr__())
        return True

    def execute_jz(self, address):
        if self.data_path.alu.z_flag:
            self.data_path.signal_latch_data_stack_top1(address)
            self.tick()

            self.data_path.pc = self.data_path.data_stack_top1
            self.tick()

            logging.debug("%s", self.__repr__())
            return True

        logging.debug("%s", self.__repr__())
        return True

    def execute_jnz(self, address):
        if not self.data_path.alu.z_flag:
            self.data_path.signal_latch_data_stack_top1(address)
            self.tick()

            self.data_path.pc = self.data_path.data_stack_top1
            self.tick()

            logging.debug("%s", self.__repr__())
            return True

        logging.debug("%s", self.__repr__())
        return True

    def execute_call(self, address):
        self.data_path.signal_latch_data_stack_top1(address)
        self.tick()

        self.data_path.signal_latch_address_stack_top(self.data_path.pc)
        self.tick()

        self.data_path.signal_latch_pc(self.data_path.data_stack_top1)
        self.data_path.signal_write_address_stack(self.data_path.address_stack_top)
        self.tick()

        logging.debug("%s", self.__repr__())
        return True

    def execute_ret(self):
        self.data_path.signal_latch_address_stack_top(self.data_path.signal_read_address_stack())
        self.tick()

        self.data_path.signal_latch_pc(self.data_path.address_stack_top)
        self.tick()

        logging.debug("%s", self.__repr__())
        return True

    def execute_halt(self):
        logging.debug("%s", self.__repr__())
        raise StopIteration()

    def decode_and_execute_instruction(self):
        instruction = self.data_path.signal_read_memory(self.data_path.pc)
        self.tick()

        self.data_path.signal_latch_pc(self.data_path.pc + 1)
        self.tick()

        opcode = instruction["opcode"]
        operand = instruction["operand"]
        print(opcode)
        self.current_instruction = opcode
        self.current_operand = operand
        if self.decode_and_execute_control_flow_instruction(opcode, operand):
            return

        if opcode == Opcode.CMP:
            self.execute_cmp(opcode)
        elif opcode in self.data_path.alu.operations:
            if opcode in [Opcode.INC, Opcode.DEC]:
                self.execute_unary_alu_operation(opcode)
            else:
                self.execute_binary_alu_operation(opcode)
        elif opcode == Opcode.DUP:
            self.execute_dup()
        elif opcode == Opcode.OVER:
            self.execute_over()
        elif opcode == Opcode.SWITCH:
            self.execute_switch()
        elif opcode == Opcode.LIT:
            self.execute_lit(operand)
        elif opcode == Opcode.PUSH:
            self.execute_push()
        elif opcode == Opcode.POP:
            self.execute_pop()
        elif opcode == Opcode.DROP:
            self.execute_drop()

    def execute_unary_alu_operation(self, opcode):
        operand = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top1(operand)
        self.tick()

        value = self.data_path.alu.compute(self.data_path.data_stack_top1, 0, opcode)
        self.data_path.signal_latch_data_stack_top1(value)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top1)
        self.tick()

        logging.debug("%s", self.__repr__())

    def execute_binary_alu_operation(self, opcode):
        value1 = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top1(value1)
        self.tick()

        value2 = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top2(value2)
        self.tick()

        value = self.data_path.alu.compute(self.data_path.data_stack_top1, self.data_path.data_stack_top2, opcode)
        self.data_path.signal_latch_data_stack_top1(value)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top1)
        self.tick()

        logging.debug("%s", self.__repr__())

    def execute_dup(self):
        operand = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top1(operand)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top1)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top1)
        self.tick()

        logging.debug("%s", self.__repr__())

    def execute_over(self):
        operand1 = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top1(operand1)
        self.tick()

        operand2 = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top2(operand2)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top2)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top1)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top2)
        self.tick()

        logging.debug("%s", self.__repr__())

    def execute_switch(self):
        operand1 = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top1(operand1)
        self.tick()

        operand2 = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top2(operand2)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top1)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top2)
        self.tick()

        logging.debug("%s", self.__repr__())

    def execute_cmp(self, opcode):
        value1 = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top1(value1)
        self.tick()

        value2 = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top1(value2)
        self.tick()

        self.data_path.alu.compute(self.data_path.data_stack_top1, self.data_path.data_stack_top2, opcode)
        self.data_path.signal_write_data_stack(self.data_path.data_stack_top2)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top1)
        self.tick()

        logging.debug("%s", self.__repr__())

    def execute_lit(self, operand):
        self.data_path.signal_latch_data_stack_top1(operand)
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top1)
        self.tick()

        logging.debug("%s", self.__repr__())

    def execute_push(self):
        address = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top1(address)
        self.data_path.signal_latch_address_stack_top(self.data_path.pc)
        self.tick()

        self.data_path.signal_latch_pc(self.data_path.data_stack_top1)
        self.tick()

        self.data_path.signal_latch_data_stack_top1(self.data_path.signal_read_memory(self.data_path.pc))
        self.tick()

        self.data_path.signal_write_data_stack(self.data_path.data_stack_top1)
        self.data_path.signal_latch_pc(self.data_path.address_stack_top)
        self.tick()

        logging.debug("%s", self.__repr__())

    def execute_pop(self):
        address = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top1(address)
        self.tick()

        operand = self.data_path.signal_read_data_stack()
        self.data_path.signal_latch_data_stack_top2(operand)
        self.data_path.signal_latch_address_stack_top(self.data_path.pc)
        self.tick()

        self.data_path.signal_latch_pc(self.data_path.data_stack_top1)
        self.tick()

        self.data_path.signal_write_memory(self.data_path.pc, self.data_path.data_stack_top2)
        self.tick()

        self.data_path.signal_latch_pc(self.data_path.address_stack_top)
        self.tick()

        logging.debug("%s", self.__repr__())

    def execute_drop(self):
        self.data_path.signal_latch_data_stack_top1(self.data_path.signal_read_data_stack())
        self.tick()

        logging.debug("%s", self.__repr__())

    def __repr__(self) -> str:
        registers_repr = "TICK: {:10} PC: {:10} TDS1: {:10} TDS2: {:10} TAS: {:10} Z_FLAG: {:1}".format(
            str(self.tick_counter),
            str(self.data_path.pc),
            str(self.data_path.data_stack_top1),
            str(self.data_path.data_stack_top2),
            str(self.data_path.address_stack_top),
            int(self.data_path.alu.z_flag),
        )

        data_stack_repr = "DATA_STACK: {}".format(self.data_path.data_stack)
        address_stack_repr = "ADDRESS_STACK: {}".format(self.data_path.address_stack)

        instruction_repr = self.current_instruction.mnemonic

        if self.current_operand is not None:
            instruction_repr += " {}".format(self.current_operand)

        return "{} \t{}\n\t   {}\n\t   {}".format(registers_repr, instruction_repr, data_stack_repr, address_stack_repr)


def simulation(machine_code, input_tokens):
    data_path = DataPath(machine_code, input_tokens)
    control_unit = ControlUnit(data_path)

    control_unit.initialization()

    instruction_counter = 0

    try:
        while instruction_counter < 2000:
            control_unit.decode_and_execute_instruction()
            instruction_counter += 1
    except StopIteration:
        pass

    return data_path.output_buffer, instruction_counter, control_unit.tick_counter


def main(machine_code_file, input_file):
    machine_code = read_code(machine_code_file)
    with open(input_file, encoding="utf-8") as f:
        input_text = f.read().strip()
        input_tokens = []
        for i in range(len(input_text)):
            input_tokens.append(input_text[len(input_text) - i - 1])
        input_tokens.append(len(input_text))

    output, instruction_counter, ticks = simulation(machine_code, input_tokens)

    print("".join(output) + "\n")
    print(f"instr_counter: {instruction_counter} ticks: {ticks}")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Invalid usage: python3 machine.py <code_file> <input_file>"
    _, machine_code_file, input_file = sys.argv
    main(machine_code_file, input_file)
