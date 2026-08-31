"""Write > Generate > Compile, with the segment MP3s kept in a temporary directory."""

import random
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .compile import Pauses, compile_podcast
from .generate import GenerateError, Synthesizer, elevenlabs_synthesize, generate
from .writer import Writer, anthropic_write, choose_expert, episode_basename, write_script


@dataclass(frozen=True)
class Episode:
    mp3: Path
    script_json: Path
    script_markdown: Path


def run(
    subject: str,
    voices: dict[str, str],
    output_directory: Path,
    expert: str | None = None,
    episode: int | None = None,
    pauses: Pauses = Pauses(),
    write: Writer = anthropic_write,
    synthesize: Synthesizer = elevenlabs_synthesize,
    rng: random.Random | None = None,
    log: Callable[[str], None] = lambda message: None,
) -> Episode:
    rng = rng or random.Random()
    expert = expert or choose_expert(rng)
    log(f"writing script about {subject!r} with {expert} as the expert")
    script = write_script(subject, expert, write=write, log=log)
    log(f"script: \"{script.title}\", {len(script.lines)} lines")

    missing = sorted({line.speaker for line in script.lines} - voices.keys())
    if missing:
        raise GenerateError("no voice specified for speaker(s): " + ", ".join(missing) + " (use --voice-NAME=VOICE-ID)")

    output_directory.mkdir(parents=True, exist_ok=True)
    basename = episode_basename(script.title, episode)
    script_json = output_directory / f"{basename}.json"
    script_markdown = output_directory / f"{basename}.md"
    script_json.write_text(script.to_json(), encoding="utf-8")
    script_markdown.write_text(script.to_markdown(), encoding="utf-8")
    log(f"wrote {script_json} and {script_markdown}")

    with tempfile.TemporaryDirectory(prefix="horizon-") as temporary:
        segments = generate(script.lines, voices, Path(temporary), synthesize=synthesize, log=log)
        log(f"generated {len(segments)} segment(s); compiling")
        output = compile_podcast(Path(temporary), output_directory / f"{basename}.mp3", pauses, rng=rng, log=log)
    return Episode(mp3=output, script_json=script_json, script_markdown=script_markdown)
