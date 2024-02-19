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
parser.add_argument("-t", "--test", help="For help during debugging.", action="store_true", default=False)
args = parser.parse_args()
# -------------------------------------------------------------- #


class Block:
    def __init__(self, offset, length, char=''):
        self.offset = offset
        self.length = length
        self.char = char

    def __str__(self):
        if self.char:
            return f'({self.offset}, {self.length}, {self.char})'
        return f'({self.offset}, {self.length})'

    def __repr__(self):
        return str(self)


def encode(string, look_ahead=15, back_search=15):
    """
    used image from:
     https://codereview.stackexchange.com/questions/233865/lz77-compression-algorithm-general-code-efficiency
    """
    result = []

    end = len(string)
    i = 0
    while i < end:
        char = string[i]
        look_back = 0
        length = 0

        if DEBUG:
            back_buff = string[i-back_search:i]
            ahead_buff = string[i:i+look_ahead]

        # for each char in the back_search_buffer
        for j in range(max(i-back_search, 0), i):
            curr_len = 0
            curr_search_idx = j

            if DEBUG:
                string_j = string[j]
                string_j_len = string[j + curr_len]
                string_i_len = string[i + curr_len]

            # get the length of current match
            while ((i + curr_len < end) and
                   (curr_len < look_ahead) and
                   (curr_search_idx < i) and
                   (string[j + curr_len] == string[i + curr_len])):
                curr_len += 1
                curr_search_idx += 1

            if curr_len > length:
                look_back = i - j
                length = curr_len
                char = string[min(i + length, end-1)]

                # special case scenario if the last match is perfectly at the end, so no next char exists
                if i + length == end:
                    char = ''

        result.append(Block(look_back, length, char))
        i += length+1
    return result


def decode(list_of_blocks):
    result = ''
    for block in list_of_blocks:
        if block.length == 0:
            result += block.char
        else:
            start = len(result) - block.offset
            end = start + block.length
            result += result[start:end]
            if block.char:
                result += block.char
    return result


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
    print('Original:', test_str)
    encoded = encode(test_str)
    print('Encoded:', encoded)

    decoded = decode(encoded)
    print('Decoded:', decoded)
    print('Original == Decoded:', test_str == decoded)


if __name__ == '__main__':
    DEBUG = args.test
    # test_decode()
    main()
