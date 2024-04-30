from hashlib import sha256
from tokenizer import computeWordFrequencies
 
N_GRAM_LENGTH = 3
FEATURE_HASH_LENGTH = 64    # in bits (AI tutor said 64 is good place to start)

### PRIVATE HELPER FUNCTIONS ###

def _bytestring_to_binary(bytes):
    # https://www.geeksforgeeks.org/convert-bytes-to-bits-in-python/
    # From AI tutor:
    #   1. Convert the bytes object to an integer using int.from_bytes(), specifying the byte order (typically 'big' for network order).
    #   2. Use the bin() function to convert the integer to a binary string. This string will have a prefix of '0b'.
    #   3. Slice off the '0b' prefix to get the binary string.
    return bin(int.from_bytes(bytes, byteorder='big'))[2:]

def _extract_features(tokens):
    # Convert tokens to features (e.g., n-grams)
    # Return a list of features
    features = []

    for i in range(len(tokens) - N_GRAM_LENGTH):
        features.append(tokens[i:i+N_GRAM_LENGTH])

    return features

def _get_feature_weights(features):
    # A common approach to feature weights is to use term frequency
    # Returns a dictionary where key = feature and value = feature frequency
    # Implementing term frequency for n-grams from AI tutor:
    #   1. Generate N-grams: You first need to generate all possible n-grams from the text. This usually involves sliding a window of size 'n'
    #   over the words in the text and collecting the words that fall within the window at each position.
    #       a. DONE; THIS IS THE PARAM features
    #   2. Count N-grams: Count how many times each unique n-gram appears in the text. This gives you the raw frequency of each n-gram.
    #       a. USE countWordFrequencies() from tokenizer
    #   3. Calculate Term Frequency: The term frequency (TF) for each n-gram can be calculated by taking the raw frequency of the n-gram and 
    #   possibly normalizing it by the total number of n-grams in the document to prevent a bias towards longer documents.
    #       a. WILL SKIP NORMALIZATION FOR NOW BUT CAN IMPLEMENT LATER IF NECESSARY
    return computeWordFrequencies(features)

def _hash_features(features):
    # Hash each feature into a binary string
    # Return a list of binary hash strings

    hashes = []

    for feature in features:
        # encode the string to bytes
        encoded = feature.encode()

        # apply sha256
        hash_digest = sha256(encoded).digest()

        # convert hash digest to binary
        binary = _bytestring_to_binary(hash_digest)

        # truncate binary string to the first FEATURE_HASH_LENGTH bits
        binary = binary[:FEATURE_HASH_LENGTH]

        hashes.append(binary)
    
    return hashes

def _create_simhash(features, hashes, feature_weights):
    # Initialize a vector V of N elements to 0 (N is the bit length of hash)
    # For each feature and its corresponding hash
        # For each bit in the hash
            # If the bit is 1, add the feature's weight to V's corresponding element
            # If the bit is 0, subtract the feature's weight
    # Initialize simhash to an empty binary string
    # For each element in V
        # If the element is positive, append '1' to simhash
        # Else, append '0'
    # Return simhash

    v = [0] * FEATURE_HASH_LENGTH

    for i, feature in enumerate(features):
        for j, bit in enumerate(hashes[i]):
            if bit == '1':
                v[j] += feature_weights[feature]
            else:
                v[j] -= feature_weights[feature]

    simhash = ''

    for element in v:
        if element > 0:
            simhash += '1'
        else:
            simhash += '0'

    return simhash

def _calculate_hamming_distance(hash1, hash2):
    # Calculate the number of differing bits between hash1 and hash2
    # Return the Hamming distance

    # Assumes hash1 and hash2 are same length

    dist = 0

    for i in range(len(hash1)):
        if hash1[i] != hash2[i]:
            dist += 1

    return dist


### PUBLIC FUNCTIONS (CALL THESE IN SCRAPER.PY) ###

# input should be the list of tokens from tokenize()
def simhash(tokens):
    features = _extract_features(tokens)
    feature_weights = _get_feature_weights(features)
    hashes = _hash_features(features)

    return _create_simhash(features, hashes, feature_weights)


def is_near_duplicate(simhash1, simhash2, threshold):
    # Calculate the Hamming distance between simhash1 and simhash2
    # If the distance is less than or equal to the threshold, return True (near-duplicate)
    # Else, return False (not a near-duplicate)
    
    return _calculate_hamming_distance(simhash1, simhash2) <= threshold
