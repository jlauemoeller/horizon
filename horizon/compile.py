"""Step 2: merge the individual segment MP3 files into one episode with natural pauses in between."""

import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from pydub import AudioSegment

SEGMENT_RE = re.compile(r"^\d{5}\.mp3$")


class CompileError(Exception):
    pass


@dataclass(frozen=True)
class Pauses:
    """Pause durations in seconds, drawn from a normal distribution clipped to [lower, upper]."""

    lower: float = 0.2
    upper: float = 1.0
    center: float = 0.5

    def __post_init__(self) -> None:
        if self.lower < 0:
            raise CompileError("pause lower bound must not be negative")
        if self.upper < self.lower:
            raise CompileError("pause upper bound must not be smaller than the lower bound")
        if not self.lower <= self.center <= self.upper:
            raise CompileError("pause center must lie between the lower and upper bound")

    @classmethod
    def parse(cls, value: str) -> "Pauses":
        parts = value.split(":")
        if len(parts) != 3:
            raise CompileError(f"--pauses must have the form lower:upper:center, got {value!r}")
        try:
            lower, upper, center = (float(part) for part in parts)
        except ValueError:
            raise CompileError(f"--pauses values must be numbers, got {value!r}")
        return cls(lower, upper, center)

    def sample(self, rng: random.Random) -> float:
        # Two standard deviations on the widest side reach the bounds, so most
        # draws land inside naturally and only the tails get clipped.
        sigma = max(self.center - self.lower, self.upper - self.center) / 2
        if sigma == 0:
            return self.center
        return min(self.upper, max(self.lower, rng.gauss(self.center, sigma)))


def find_segments(segment_directory: Path) -> list[Path]:
    segments = [path for path in segment_directory.iterdir() if SEGMENT_RE.match(path.name)]
    if not segments:
        raise CompileError(f"no segment files (NNNNN.mp3) found in {segment_directory}")
    return sorted(segments, key=lambda path: path.name)


def compile_podcast(
    segment_directory: Path,
    output: Path,
    pauses: Pauses = Pauses(),
    rng: random.Random | None = None,
    log: Callable[[str], None] = lambda message: None,
) -> Path:
    rng = rng or random.Random()
    segments = find_segments(segment_directory)

    podcast = AudioSegment.empty()
    for index, segment in enumerate(segments):
        if index > 0:
            pause = pauses.sample(rng)
            podcast += AudioSegment.silent(duration=round(pause * 1000))
        log(f"[{index + 1}/{len(segments)}] {segment.name}")
        podcast += AudioSegment.from_mp3(segment)

    output.parent.mkdir(parents=True, exist_ok=True)
    podcast.export(output, format="mp3", bitrate="128k")
    return output
