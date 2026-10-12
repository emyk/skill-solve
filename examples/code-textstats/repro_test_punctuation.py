from textstats import top_words, word_frequencies


def test_punctuation_does_not_stick_to_words():
    assert top_words("Hello, world! Hello.") == [("hello", 2), ("world", 1)]


def test_punctuation_only_tokens_are_not_words():
    assert "-" not in word_frequencies("well - that is that")
