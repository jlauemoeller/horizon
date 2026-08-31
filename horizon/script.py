"""Script lines and their segmentation for the text-to-dialogue API."""

import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Line:
    speaker: str  # normalised: lower case, spaces replaced by dashes
    text: str

def normalise_speaker(name: str) -> str:
    return re.sub(r"\s+", "-", name.strip().lower())

MAX_SEGMENT_CHARS = 2000

# A sentence ends with ., !, ? or … (optionally followed by closing quotes/brackets) and whitespace.
_SENTENCE_RE = re.compile(r"(\S+?[.!?…][\"'”’)\]]*)(?:\s+|$)")

def split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    position = 0
    for match in _SENTENCE_RE.finditer(text):
        sentences.append(text[position:match.end(1)].strip())
        position = match.end()
    if position < len(text) and text[position:].strip():
        sentences.append(text[position:].strip())
    return [sentence for sentence in sentences if sentence]

def _split_words(text: str, limit: int) -> list[str]:
    """Last resort for a single sentence longer than the limit: break at word boundaries."""
    chunks: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if len(candidate) > limit and current:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    # A single word longer than the limit is cut hard.
    return [piece for chunk in chunks for piece in (chunk[i:i + limit] for i in range(0, len(chunk), limit))]

def split_line(line: Line, limit: int = MAX_SEGMENT_CHARS) -> list[Line]:
    """Break a line longer than `limit` into several lines for the same speaker, one sentence at a time."""
    if len(line.text) <= limit:
        return [line]
    pieces: list[str] = []
    current = ""
    for sentence in split_sentences(line.text):
        for part in ([sentence] if len(sentence) <= limit else _split_words(sentence, limit)):
            candidate = f"{current} {part}" if current else part
            if len(candidate) > limit:
                pieces.append(current)
                current = part
            else:
                current = candidate
    if current:
        pieces.append(current)
    return [Line(line.speaker, piece) for piece in pieces]

def segment_lines(lines: list[Line], limit: int = MAX_SEGMENT_CHARS) -> list[list[Line]]:
    """Group consecutive lines into segments whose total text length does not exceed `limit`.

    Each segment becomes one text-to-dialogue API request, so it may contain several speakers.
    """
    segments: list[list[Line]] = []
    current: list[Line] = []
    current_length = 0
    for line in lines:
        for piece in split_line(line, limit):
            if current and current_length + len(piece.text) > limit:
                segments.append(current)
                current, current_length = [], 0
            current.append(piece)
            current_length += len(piece.text)
    if current:
        segments.append(current)
    return segments
