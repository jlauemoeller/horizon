"""Step 1: turn script segments into individual MP3 files via the ElevenLabs text-to-dialogue API."""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from .script import Line, MAX_SEGMENT_CHARS, segment_lines

API_URL = "https://api.elevenlabs.io/v1/text-to-dialogue"
MODEL_ID = "eleven_v3"
OUTPUT_FORMAT = "mp3_44100_128"
API_KEY_ENV = "ELEVENLABS_API_KEY"

# One API input: (text, voice_id). A synthesizer turns a list of them into MP3 bytes.
DialogueInput = tuple[str, str]
Synthesizer = Callable[[list[DialogueInput]], bytes]


class GenerateError(Exception):
    pass


def segment_filename(counter: int) -> str:
    return f"{counter:05d}.mp3"


def elevenlabs_synthesize(inputs: list[DialogueInput], api_key: str | None = None) -> bytes:
    api_key = api_key or os.environ.get(API_KEY_ENV)
    if not api_key:
        raise GenerateError(f"{API_KEY_ENV} is not set in the environment")

    body = json.dumps(
        {
            "inputs": [{"text": text, "voice_id": voice_id} for text, voice_id in inputs],
            "model_id": MODEL_ID,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL + f"?output_format={OUTPUT_FORMAT}",
        data=body,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise GenerateError(f"ElevenLabs API returned {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise GenerateError(f"could not reach the ElevenLabs API: {error.reason}") from error


def generate(
    lines: list[Line],
    voices: dict[str, str],
    working_directory: Path,
    synthesize: Synthesizer = elevenlabs_synthesize,
    log: Callable[[str], None] = lambda message: None,
    limit: int = MAX_SEGMENT_CHARS,
) -> list[Path]:
    missing = sorted({line.speaker for line in lines} - voices.keys())
    if missing:
        raise GenerateError(
            "no voice specified for speaker(s): " + ", ".join(missing)
            + " (use --voice-NAME=VOICE-ID)"
        )

    segments = segment_lines(lines, limit)
    working_directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for counter, segment in enumerate(segments, start=1):
        target = working_directory / segment_filename(counter)
        characters = sum(len(line.text) for line in segment)
        log(f"[{counter}/{len(segments)}] {len(segment)} line(s), {characters} chars, starts: "
            f"{segment[0].speaker}: {segment[0].text[:40]}")
        target.write_bytes(synthesize([(line.text, voices[line.speaker]) for line in segment]))
        written.append(target)
    return written
