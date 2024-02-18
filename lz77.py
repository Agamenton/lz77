
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


def encode(string):
    result = []
    i = 0
    while i < len(string):
        offset = 0
        length = 0
        char = string[i]
        for j in range(i):
            k = 0
            while i + k < len(string) and string[j + k] == string[i + k]:
                k += 1
            if k > length:
                offset = i - j
                length = k
                char = ''
        result.append(Block(offset, length, char))
        i += max(1, length)
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
    # test_decode()
    main()
