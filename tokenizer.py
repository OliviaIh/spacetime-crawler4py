import sys

BUFFER_SIZE = 100   # number of characters to read at one time from file

'''
Turns the given file into a list of token strings. 

Reads BUFFER_SIZE number of characters at a time from the given file, breaking up the file into tokens
of only alphanumeric English characters. 

TIME COMPLEXITY: O(n)
Let n be the size of the file. Reading the file in BUFFER_SIZE chunks is O(n) because you are reading each
character in the file once. Iterating through each character in the buffer ultimately means reading each
character in the file a second time, bringing the total time complexity to O(2n). Appending to an array is
O(1), so append() calls can be ignored. The string operations that are used in the for-loop (isalnum(), 
isascii(), lower(), len()) are all of linear complexity with respect to the length of the input string.
Since these operations are called on single characters or small fragments of the file, they will only add
some O(kn) time complexity, where k is some constant. Thus, the overall time complexity of tokenize() is
O((2+k)n), which can be simplified to O(n).
'''
def tokenize(file: str):
    tokens = []
    current_token = ""

    with open(file, 'r') as f:
        while True:
            buffer = f.read(BUFFER_SIZE)    # read BUFFER_SIZE number of chars from f

            if buffer == '':
                break   # EOF

            # not EOF
            # go through each character in buffer
            for c in buffer:
                # isalnum() checks for alphanumeric characters and isascii() checks for ASCII/English characters
                if not c.isalnum() or not c.isascii() or c != "'":
                    # only add to tokens if non-empty string
                    if len(current_token) > 0:
                        tokens.append(current_token)
                    
                    current_token = ""
                else:
                    current_token += c.lower()  # make everything lowercase so tokens are case-insensitive

            if len(buffer) < BUFFER_SIZE:
                # no more text to read after this buffer --> whatever is in current_token is the last token
                if len(current_token) > 0:
                    tokens.append(current_token)
        
    return tokens


'''
Turns the given list of token strings into a dictionary whose keys are unique tokens and values are the frequency
of the key/token.

Iterates through the list of tokens and either inserts a new key-value pair into a dictionary or increments the
existing key-value pair's value, then returns the dictionary.

TIME COMPLEXITY: O(n)
Let n be the number of tokens. Iterating through each token in the list is O(n), checking for a key in a dictionary
is O(1), and inserting into a dictionary is O(1). Thus, the overall time complexity of computeWordFrequencies()
is O(n).
'''
def computeWordFrequencies(tokens: list):
    freqs = {}

    for token in tokens:
        if token in freqs:
            freqs[token] += 1   # increment count if token already seen
        else:
            freqs[token] = 1    # initialize count of new token to 1

    return freqs


'''
Prints the given token frequencies dictionary (keys = token strings, values = integer frequencies) to the console,
where each key-value pair has the format '<token> <freq>' and is printed on a new line. Frequencies are printed
in descending order of frequency with ascending lexicographical order as a tiebreaker.

Sorts the given token frequencies dictionary into a list, then iterates through the list and prints out the key-value
pair in the correct format.

TIME COMPLEXITY: O(n log n)
Let n be the number of tokens in the given dictionary. It takes O(n log n) time to sort the dictionary and O(n) time
to iterate through the dictionary to print. Therefore, the overall time complexity of printWordFrequencies() is
O(n log n).
'''
def printWordFrequencies(freqs: dict):
    # use of sorted is based on https://runestone.academy/ns/books/published/fopp/Sorting/SecondarySortOrder.html
    freqs_sorted = sorted(freqs.items(), key=lambda x: (-x[1], x[0]))

    for freq in freqs_sorted:
        print(f'{freq[0]} {freq[1]}')


'''
The function that gets called when this script is run in the command line. Parses the command line arguments
for the filepath and calculates and outputs the file's token frequencies.

If no filepaths are given, the program prints a message to the user asking for them to provide a filepath,
then exits. If 1 or more filepaths are given, the program will parse out the first filepath, ignore any extra
filepaths/arguments, then proceed with calculating and outputting the first file's token frequencies.

TIME COMPLEXITY: O(n + m + m log m)
len(sys.argv) is linearly complex with respect to the number of arguments given, and accessing array elements
and printing are all constant operations. Assuming a relatively small number of arguments are given, the
processing of sys.argv and exception-handling is essentially constant. Most of the time will be spent on tokenize(),
computeWordFrequencies(), and printWordFrequencies(), which have time complexities of O(n), O(m), and O(m log m),
respectively, where n is the size of the file and m is the number of tokens in the file. Thus, the total time
complexity for runPartA() is O(n + m + m log m).
'''
def runPartA():
    if len(sys.argv) < 2:   # no filepaths given
        print("Please provide a filepath.")
    else: # at least 1 filepath given
        file = sys.argv[1]

        try:
            tokens_list = tokenize(file)
            tokens_freq = computeWordFrequencies(tokens_list)
            printWordFrequencies(tokens_freq)
        except OSError as e:
            print(f"Error with reading {file}.")

if __name__ == '__main__':
    runPartA()