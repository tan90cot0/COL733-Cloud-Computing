def load_words():
    # From https://docs.oracle.com/javase/tutorial/collections/interfaces/examples/dictionary.txt
    with open('dictionary.txt') as word_file:
        valid_words = set(word_file.read().split())
    return valid_words
