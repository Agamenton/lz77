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


def encode(data, look_ahead=MAX_WINDOW/2, back_search=MAX_WINDOW/2):
    """
    used image from:
     https://codereview.stackexchange.com/questions/233865/lz77-compression-algorithm-general-code-efficiency
    """
    if look_ahead % 2:
        look_ahead += 1
    if look_ahead > MAX_WINDOW/2:
        look_ahead = MAX_WINDOW/2

    if back_search % 2:
        back_search += 1
    if back_search > MAX_WINDOW/2:
        back_search = MAX_WINDOW/2

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
        offset = 0
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
                offset = i - j
                length = curr_len
                byte = data[min(i + length, end - 1)]

                # special case scenario if the last match is perfectly at the end, so no next char exists
                if i + length == end:
                    byte = 0

        result.append(offset)
        result.append(length)
        result.append(byte)
        i += length+1
    return bytes(result)


def decode(list_of_bytes: bytes):
    S_OFFSET = 0
    S_LENGTH = 1
    S_BYTE = 2

    result = []
    state = S_OFFSET

    offset = 0
    length = 0
    for byte in list_of_bytes:
        if state == S_OFFSET:
            offset = byte
            state = S_LENGTH
        elif state == S_LENGTH:
            length = byte
            state = S_BYTE
        else:
            if (not length == 0) and (not offset == 0):
                start = len(result) - offset
                end = start + length
                result.extend(result[start:end])
            result.append(byte)
            state = S_OFFSET

    return bytes(result[:-1])   # ignore last byte because my encoding always puts \x00 at end


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
    expected = [0,1,1,2,1,1,2,2]
    encoded = [0,0,0,
               0,0,1,
               1,1,2,
               3,3,2]
    decoded = decode(bytes(encoded))
    for d in decoded:
        print(int(d))
    print(decoded == bytes(expected))


def main():
    # ----- INPUT ------
    test_str = 'abracadabra'
    in_f = "i.txt"
    out_f = f"{in_f}.lz77"
    with open(in_f, "rb") as f:
        test_str = f.read()
    print(f'Original size: {sys.getsizeof(test_str)}B')

    # ----- ENCODE ------
    start = time.time()
    encoded = encode(test_str, look_ahead=30, back_search=30)
    end = time.time()
    elapsed = end - start
    print(f'({elapsed:.2f}s) Encoded size: {sys.getsizeof(encoded)}B')
    with open(out_f, "wb") as f:
        f.write(encoded)

    # ----- DECODE ------
    decoded = decode(encoded)
    print(f'Decoded size: {sys.getsizeof(decoded)}B')
    print(f'Original == Decoded: {test_str == decoded}')
    with open("decoded.txt", "wb") as f:
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
    main()
    # test()


