from collections import Counter

from .tokenize import tokenize


def word_frequencies(text):
    """Return a Counter mapping each word to how often it occurs."""
    return Counter(tokenize(text))


def top_words(text, n=3):
    """Return the n most common (word, count) pairs, most common first."""
    return word_frequencies(text).most_common(n)


def average_word_length(text):
    """Average length of the words in text, or 0.0 for empty text."""
    words = tokenize(text)
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)
