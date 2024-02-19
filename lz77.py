import math
import sys
import time
import argparse


# -------------------------------------------------------------- #
# ---------------------- ARGUMENTS PARSER ---------------------- #
# -------------------------------------------------------------- #
parser = argparse.ArgumentParser(
    description="""Compression algorithm LZ77."""
)
parser.add_argument("input", nargs="?", default=None)
parser.add_argument("-o", "--output", help="Specify output file name/path, otherwise [input].lz77 will be used.",
                    default=None)
parser.add_argument("-s", "--string", help="""If used, then expects the input to be a string and not a filepath and the string will be compressed.
The '-o' argument must be specified.""", action="store_true", default=False)
parser.add_argument("-d", "--decompress", help="If used, then the input is expected to be a compressed file_path/string.",
                    action="store_true", default=False)
parser.add_argument("-t", "--test", help="For help during debugging.", action="store_true",
                    default=False)
parser.add_argument("-w", "--window", help="Specify the window size, cannot be less then 4 and more than 127.",
                    default=None)
args = parser.parse_args()
# -------------------------------------------------------------- #


class Block:
    def __init__(self, offset, length, byte=0):
        self.offset = offset
        self.length = length
        self.byte = byte

    def __str__(self):
        if self.byte:
            return f'({self.offset}, {self.length}, {self.byte})'
        return f'({self.offset}, {self.length})'

    def __repr__(self):
        return str(self)


LARGEST_NUMBER = 0
MAX_WINDOW = 127


def encode(data, look_ahead=15, back_search=15):
    """
    used image from:
     https://codereview.stackexchange.com/questions/233865/lz77-compression-algorithm-general-code-efficiency
    """
    global LARGEST_NUMBER
    look_ahead = min(look_ahead, MAX_WINDOW)
    back_search = min(back_search, MAX_WINDOW)

    result = []

    end = len(data)
    i = 0
    start = time.time()
    one_percent = end / 100
    while i < end:
        now = time.time()
        elapsed = now-start
        percent = (i / one_percent) + 1
        print(f"({elapsed:.2f}s) {percent:.2f}%", end="\r")

        byte = data[i]
        look_back = 0
        length = 0

        if DEBUG:
            back_buff = data[i - back_search:i]
            ahead_buff = data[i:i + look_ahead]

        # for each char in the back_search_buffer
        for j in range(max(i-back_search, 0), i):
            curr_len = 0
            curr_search_idx = j

            if DEBUG:
                string_j = data[j]
                string_j_len = data[j + curr_len]
                string_i_len = data[i + curr_len]

            # get the length of current match
            while ((i + curr_len < end) and
                   (curr_len < look_ahead) and
                   (curr_search_idx < i) and
                   (data[j + curr_len] == data[i + curr_len])):
                curr_len += 1
                curr_search_idx += 1

            if curr_len > length:
                look_back = i - j
                length = curr_len
                byte = data[min(i + length, end - 1)]

                # special case scenario if the last match is perfectly at the end, so no next char exists
                if i + length == end:
                    byte = 0

        LARGEST_NUMBER = max(LARGEST_NUMBER, length)
        LARGEST_NUMBER = max(LARGEST_NUMBER, look_back)

        result.append(Block(look_back, length, byte))
        i += length+1
    return result


def decode(list_of_blocks):
    result = ''
    for block in list_of_blocks:
        if block.length == 0:
            result += block.byte
        else:
            start = len(result) - block.offset
            end = start + block.length
            result += result[start:end]
            if block.byte:
                result += block.byte
    return result


def to_bin_file(out_file, data: list[Block]):
    bits_per_symbol = math.log2(LARGEST_NUMBER)
    if bits_per_symbol % 1:
        bits_per_symbol += 1
    bits_per_symbol = int(bits_per_symbol)
    if DEBUG:
        print(f"bits_per_symbol={bits_per_symbol}")

    result = [LARGEST_NUMBER]
    next_byte = 0
    shift = 0
    for i, block in enumerate(data):
        look_ahead = Block(0, 0, 0)
        if i < len(data)-1:
            look_ahead = data[i+1]

        # flags to represent progress of current block
        curr_offset = False
        curr_length = False
        curr_byte = False
        split_rest = 0
        split_switch = None

        MAX_SHIFT = 7
        SWITCH_OFFSET = "_offset_"
        SWITCH_LENGTH = "_length_"
        SWITCH_BYTE = "_byte_"

        while (not curr_offset) and (not curr_length) and (not curr_byte):

            # if this byte still has space for another value
            while (MAX_SHIFT - shift) > bits_per_symbol:

                # first check previously split value (can only happen with filling new empty byte)
                if split_rest:
                    if split_switch == SWITCH_OFFSET:
                        next_byte = block.offset << (MAX_SHIFT - (split_rest - 1))
                        curr_offset = True
                    elif split_switch == SWITCH_LENGTH:
                        next_byte = block.length << (MAX_SHIFT - (split_rest - 1))
                        curr_length = True
                    else:
                        next_byte = block.byte << (MAX_SHIFT - (split_rest - 1))
                        curr_byte = True
                    shift = split_rest
                    split_rest = 0
                    split_switch = None

                if not curr_offset:
                    next_byte = next_byte | block.offset << bits_per_symbol
                    curr_offset = True
                    shift += bits_per_symbol

                elif not curr_length:
                    next_byte = next_byte | block.length << bits_per_symbol
                    curr_length = True
                    shift += bits_per_symbol

                # this only happens if offset and length were previously recorded and the byte has it's own byte
                elif (not curr_byte) and (shift == 0):
                    next_byte = block.byte
                    curr_byte = True
                    shift += MAX_SHIFT

            # now the byte cannot store the next full information
            free_bits = MAX_SHIFT - shift + 1
            free_shift = free_bits - 1
            if free_bits:
                # split value
                if not curr_offset:
                    next_byte = next_byte | (block.offset >> (bits_per_symbol-free_bits))


            else:
                result.append(next_byte)
                next_byte = 0



def test_decode():

    encoded = [Block(0, 0, 'a'),
               Block(0, 0, 'b'),
               Block(1, 1),
               Block(1, 1),
               Block(4, 3)]
    decoded = decode(encoded)
    expected = 'abbbabb'
    print('Decoded:', decoded)
    print('Expected:', expected)
    print(f'Test decode success? {decoded == expected}')


def main():
    test_str = 'abracadabra'
    in_f = "i.txt"
    out_f = "i.lz77"
    with open(in_f, "r") as f:
        test_str = f.read()
    print(f'Original size: {sys.getsizeof(test_str)}B')
    start = time.time()
    encoded = encode(test_str, look_ahead=30, back_search=30)
    end = time.time()
    elapsed = end - start
    print(f'({elapsed:.2f}s) Encoded size: {sys.getsizeof(encoded)}B')
    with open(out_f, "w") as f:
        for block in encoded:
            f.write(f"{block}\n")

    decoded = decode(encoded)
    print(f'Decoded size: {sys.getsizeof(decoded)}B')
    print(f'Original == Decoded: {test_str == decoded}')
    with open("decoded.txt", "w") as f:
        f.write(decoded)


def test():
    test_str = 'abracadabradabracadabrad'
    print(f'Original size: {sys.getsizeof(test_str)}B')
    start = time.time()
    encoded = encode(test_str, look_ahead=5, back_search=7)
    end = time.time()
    elapsed = end - start
    print(f'({elapsed:.2f}s) Encoded size: {sys.getsizeof(encoded)}B')
    for b in encoded:
        print(b)

    decoded = decode(encoded)
    print(f'Decoded size: {sys.getsizeof(decoded)}B')
    print(f'Original == Decoded: {test_str == decoded}')


if __name__ == '__main__':
    DEBUG = args.test
    # test_decode()
    # main()
    test()
    # to_bin_file("a", "a")

    with open("i.txt", "rb") as f:
        data = f.read()

    print(type(data))
    print(data[0])
    print(type(data[0]))
    print(data[1])
    print(data[2])


