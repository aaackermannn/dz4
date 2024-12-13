import csv
import struct
import argparse


def assemble(input_path, output_path, log_path):
    """
    Ассемблирует текстовую программу в бинарный файл и логирует команды в формате CSV.
    """
    with open(input_path, 'r') as f:
        lines = f.readlines()

    binary_instructions = []
    log_data = []

    for line in lines:
        parts = line.strip().split()
        command = parts[0]
        args = list(map(int, parts[1:]))

        if command == "LOAD_CONST":
            # Команда загрузки константы (A=5, B=адрес, C=константа)
            A = 5
            B, C = args
            instruction = ((A & 0x7) << 61) | ((B & 0xFFFFF) << 41) | (C & 0x7FFFFFFFFFF)
        elif command == "READ_MEM":
            # Чтение значения из памяти (A=6, B=адрес1, C=адрес2, D=смещение)
            A = 6
            B, C, D = args
            instruction = ((A & 0x7) << 61) | ((B & 0xFFFFF) << 41) | ((C & 0xFFFFF) << 21) | (D & 0x7FFF)
        elif command == "WRITE_MEM":
            # Запись значения в память (A=1, B=адрес1, C=адрес2)
            A = 1
            B, C = args
            instruction = ((A & 0x7) << 61) | ((B & 0xFFFFF) << 41) | (C & 0xFFFFF)
        elif command == "ABS":
            # Унарная операция abs() (A=0, B=адрес1, C=адрес2)
            A = 0
            B, C = args
            instruction = ((A & 0x7) << 61) | ((B & 0xFFFFF) << 41) | (C & 0xFFFFF)
        else:
            raise ValueError(f"Unknown command: {command}")

        binary_instructions.append(instruction)
        log_data.append({'command': command, 'args': args, 'instruction': f"{instruction:016X}"})

    with open(output_path, 'wb') as f:
        for inst in binary_instructions:
            f.write(inst.to_bytes(8, byteorder='big'))

    with open(log_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['command', 'args', 'instruction'])
        writer.writeheader()
        writer.writerows(log_data)


def interpret(binary_path, memory_dump_path, memory_range):
    """
    Интерпретирует бинарный файл и сохраняет значения диапазона памяти в формате CSV.
    """
    with open(binary_path, 'rb') as f:
        instructions = f.read()

    memory = [0] * 1024
    for i in range(0, len(instructions), 8):
        instruction = int.from_bytes(instructions[i:i + 8], byteorder='big')
        A = (instruction >> 61) & 0x7
        B = (instruction >> 41) & 0xFFFFF
        C = (instruction >> 21) & 0xFFFFF
        D = instruction & 0x7FFF

        if A == 5:  # LOAD_CONST
            memory[B] = C
        elif A == 6:  # READ_MEM
            memory[B] = memory[memory[C] + D]
        elif A == 1:  # WRITE_MEM
            memory[memory[B]] = memory[memory[C]]
        elif A == 0:  # ABS
            memory[memory[B]] = abs(memory[memory[C]])

    memory_dump = memory[memory_range[0]:memory_range[1]]
    with open(memory_dump_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Address', 'Value'])
        for address, value in enumerate(memory_dump, start=memory_range[0]):
            writer.writerow([address, value])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assembler and Interpreter for UVM")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Ассемблер
    asm_parser = subparsers.add_parser("assemble", help="Run assembler")
    asm_parser.add_argument('--input', required=True, help="Path to input file")
    asm_parser.add_argument('--output', required=True, help="Path to binary output file")
    asm_parser.add_argument('--log', required=True, help="Path to log file")

    # Интерпретатор
    int_parser = subparsers.add_parser("interpret", help="Run interpreter")
    int_parser.add_argument('--binary', required=True, help="Path to binary input file")
    int_parser.add_argument('--result', required=True, help="Path to result file")
    int_parser.add_argument('--memory_range', nargs=2, type=int, required=True, help="Memory range to dump")

    args = parser.parse_args()

    if args.mode == "assemble":
        assemble(args.input, args.output, args.log)
    elif args.mode == "interpret":
        interpret(args.binary, args.result, args.memory_range)
