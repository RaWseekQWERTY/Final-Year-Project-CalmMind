import numpy as np
import nltk
from nltk.stem.porter import PorterStemmer
nltk.download('punkt_tab')

# Initialize the stemmer
stemmer = PorterStemmer()

def tokenize(sentence):
    """
    Tokenize the input sentence using NLTK's word_tokenize.
    :param sentence: str, input sentence
    :return: list of tokens (words)
    """
    return nltk.word_tokenize(sentence)

def stem(word):
    """
    Stem a word using the Porter stemmer.
    :param word: str, word to be stemmed
    :return: str, stemmed word
    """
    return stemmer.stem(word.lower())

def bag_of_words(tokenized_sentence, all_words):
    """
    Create a bag-of-words representation of the tokenized sentence.
    :param tokenized_sentence: list of words from the input sentence
    :param all_words: list of all unique words from the training data
    :return: NumPy array of shape (len(all_words),) with 1s and 0s indicating presence of words
    """
    # Stem each word in the tokenized sentence
    sentence_words = [stem(word) for word in tokenized_sentence]

    # Initialize the bag with zeros
    bag = np.zeros(len(all_words), dtype=np.float32)

    # Set 1 for each word in the sentence that exists in all_words
    for idx, w in enumerate(all_words):
        if w in sentence_words:
            bag[idx] = 1

    return bag