import sys
import time
import argparse


LARGEST_NUMBER = 0
MAX_WINDOW = 510


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
parser.add_argument("-w", "--window", help="Specify the window size, cannot be less then 4 and more than 510.",
                    default=MAX_WINDOW)
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


def encode(data, look_ahead=args.window/2, back_search=args.window/2):
    """
    used image from:
     https://codereview.stackexchange.com/questions/233865/lz77-compression-algorithm-general-code-efficiency
    """
    if look_ahead % 2:
        look_ahead += 1
    if look_ahead > MAX_WINDOW/2:
        look_ahead = MAX_WINDOW//2

    if back_search % 2:
        back_search += 1
    if back_search > MAX_WINDOW/2:
        back_search = MAX_WINDOW//2

    result = []

    end = len(data)
    i = 0
    start = time.time()
    one_percent = end / 100
    while i < end:
        # now = time.time()
        # elapsed = now-start
        # percent = (i / one_percent) + 1
        # print(f"({elapsed:.2f}s) {percent:.2f}%", end="\r")

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


def main():
    # ----- INPUT ------
    in_f = args.input if args.input else "i.txt"
    out_f = f"{in_f}.lz77"
    with open(in_f, "rb") as f:
        input_bytes = f.read()
    original_size = sys.getsizeof(input_bytes)
    print(f'Original size: {original_size}B')

    # ----- ENCODE ------
    start = time.time()

    encoded = encode(input_bytes)

    end = time.time()
    elapsed = end - start

    print(f'({elapsed:.2f}s) Encoded size: {sys.getsizeof(encoded)}B')
    with open(out_f, "wb") as f:
        f.write(encoded)

    # ----- DECODE ------
    decoded = decode(encoded)
    print(f'Decoded size: {sys.getsizeof(decoded)}B')
    print(f'Original == Decoded: {input_bytes == decoded}')
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


if __name__ == '__main__':
    DEBUG = args.test
    # test_decode()
    main()
    # test()
    # to_bin_file("a", "a")


