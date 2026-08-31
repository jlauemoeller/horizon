from horizon.script import Line, normalise_speaker, segment_lines, split_line, split_sentences


def test_speaker_names_are_normalised():
    assert normalise_speaker("Mary Ann") == "mary-ann"
    assert normalise_speaker(" Carl ") == "carl"


def test_split_sentences():
    assert split_sentences('One. Two! "Three?" Four… five.') == ["One.", "Two!", '"Three?"', "Four…", "five."]


def test_short_line_is_not_split():
    line = Line("carl", "Short line.")
    assert split_line(line, limit=20) == [line]


def test_long_line_is_split_one_sentence_at_a_time():
    line = Line("carl", "First sentence here. Second one. Third sentence is here. Fourth.")
    pieces = split_line(line, limit=35)
    assert all(piece.speaker == "carl" for piece in pieces)
    assert [piece.text for piece in pieces] == [
        "First sentence here. Second one.",
        "Third sentence is here. Fourth.",
    ]


def test_oversized_sentence_is_split_at_word_boundaries():
    line = Line("carl", "this sentence has no punctuation and just keeps going on and on")
    pieces = split_line(line, limit=20)
    assert " ".join(piece.text for piece in pieces) == line.text
    assert all(len(piece.text) <= 20 for piece in pieces)


def test_segment_lines_packs_greedily_within_limit():
    lines = [Line("a", "x" * 900), Line("b", "y" * 900), Line("a", "z" * 300), Line("b", "w" * 1900)]
    segments = segment_lines(lines, limit=2000)
    assert [[line.text[0] for line in segment] for segment in segments] == [["x", "y"], ["z"], ["w"]]


def test_segment_lines_splits_long_lines_and_keeps_order():
    long = ("Alpha beta. " * 300).strip()
    lines = [Line("a", "Intro."), Line("b", long), Line("a", "Outro.")]
    segments = segment_lines(lines, limit=2000)
    flat = [line for segment in segments for line in segment]
    assert [line.speaker for line in flat] == ["a", "b", "b", "a"]
    assert " ".join(line.text for line in flat[1:3]) == long
    assert all(sum(len(line.text) for line in segment) <= 2000 for segment in segments)
