from textstats import word_frequencies, top_words, average_word_length


def test_counts_repeated_words():
    assert word_frequencies("a b a")["a"] == 2


def test_case_insensitive():
    assert word_frequencies("Cat cat CAT")["cat"] == 3


def test_top_words_order():
    assert top_words("x y y z z z", n=2) == [("z", 3), ("y", 2)]


def test_average_word_length_empty():
    assert average_word_length("") == 0.0


def test_average_word_length_simple():
    assert average_word_length("ab abcd") == 3.0
