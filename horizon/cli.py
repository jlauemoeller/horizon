"""Command line interface: `horizon --subject=... --voice-carl=... --voice-linda=... [...]`."""

import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__
from .compile import CompileError, Pauses
from .generate import GenerateError
from .pipeline import run
from .script import normalise_speaker
from .writer import HOSTS, WriterError

DEFAULT_VOICES = {"carl": "UgBBYS2sOqTuMpoF3BR0", "linda": "OZxMHsGaBmV5pjMIDIn0"}

USAGE = f"""horizon {__version__} - write a podcast episode with Claude and voice it with ElevenLabs

Usage:
  horizon [--subject=TEXT] [--voice-carl=VOICE-ID] [--voice-linda=VOICE-ID]
           [--expert=carl|linda] [--episode=N] [--output-directory=PATH] [--pauses=LOWER:UPPER:CENTER]

Options:
  --subject=TEXT              Subject of the episode (default: read from stdin until EOF)
  --voice-SPEAKER=VOICE-ID    ElevenLabs voice for SPEAKER (carl or linda); defaults:
                                carl  {DEFAULT_VOICES["carl"]}
                                linda {DEFAULT_VOICES["linda"]}
  --expert=carl|linda         Host who plays the subject matter expert (default: chosen at random)
  --episode=N                 Episode number, used as a prefix of the output file names
  --output-directory=PATH     Where to write the episode MP3 and its script (default: episodes)
  --pauses=LOWER:UPPER:CENTER Pause between dialogue segments, seconds (default 0.2:1.0:0.5)

The episode is written to <episode>_<title>.mp3 next to the script as .json and .md.
API keys are read from ANTHROPIC_API_KEY and ELEVENLABS_API_KEY.
"""

VOICE_PREFIX = "--voice-"


class UsageError(Exception):
    pass


@dataclass
class Options:
    subject: str = ""
    expert: str | None = None
    episode: int | None = None
    output_directory: Path = Path("episodes")
    pauses: Pauses = field(default_factory=Pauses)
    voices: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_VOICES))


def parse_args(argv: list[str]) -> Options:
    if argv and argv[0] in ("-h", "--help"):
        raise UsageError("")

    options = Options()
    for arg in argv:
        if not arg.startswith("--") or "=" not in arg:
            raise UsageError(f"options must have the form --name=value, got {arg!r}")
        name, value = arg.split("=", 1)
        if not value:
            raise UsageError(f"option {name} requires a value")

        if name.startswith(VOICE_PREFIX):
            speaker = normalise_speaker(name[len(VOICE_PREFIX):])
            if not speaker:
                raise UsageError("--voice- option is missing the speaker name")
            options.voices[speaker] = value
        elif name == "--subject":
            options.subject = value.strip()
        elif name == "--expert":
            expert = value.strip().capitalize()
            if expert not in HOSTS:
                raise UsageError(f"--expert must be one of {', '.join(host.lower() for host in HOSTS)}, got {value!r}")
            options.expert = expert
        elif name == "--episode":
            if not value.isdigit():
                raise UsageError(f"--episode must be a non-negative integer, got {value!r}")
            options.episode = int(value)
        elif name == "--output-directory":
            options.output_directory = Path(value)
        elif name == "--pauses":
            options.pauses = Pauses.parse(value)
        else:
            raise UsageError(f"unknown option {name}")

    return options


def read_subject(stream=None) -> str:
    """Read the episode subject from `stream` (default stdin) up to EOF."""
    stream = sys.stdin if stream is None else stream
    if stream.isatty():
        log("no --subject given; reading the subject from stdin (finish with Ctrl-D)")
    subject = stream.read().strip()
    if not subject:
        raise UsageError("--subject was not given and nothing was read from stdin")
    return subject


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        if not argv and sys.stdin.isatty():
            raise UsageError("")
        options = parse_args(argv)
        if not options.subject:
            options.subject = read_subject()
        episode = run(
            options.subject,
            options.voices,
            options.output_directory,
            expert=options.expert,
            episode=options.episode,
            pauses=options.pauses,
            log=log,
        )
        log(f"wrote {episode.mp3}")
        return 0
    except UsageError as error:
        print(USAGE, file=sys.stderr)
        if str(error):
            print(f"error: {error}", file=sys.stderr)
            return 2
        return 0
    except (WriterError, GenerateError, CompileError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
