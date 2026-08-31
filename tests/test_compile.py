import random

import pytest
from pydub import AudioSegment
from pydub.generators import Sine

from horizon.compile import CompileError, Pauses, compile_podcast, find_segments


def tone(path, duration_ms=300):
    Sine(440).to_audio_segment(duration=duration_ms).export(path, format="mp3")


def test_pauses_parse():
    assert Pauses.parse("0.1:2.0:0.7") == Pauses(0.1, 2.0, 0.7)


@pytest.mark.parametrize("value", ["1:2", "a:b:c", "1.0:0.5:0.7", "0.2:1.0:1.5", "-1:1:0"])
def test_pauses_reject_bad_values(value):
    with pytest.raises(CompileError):
        Pauses.parse(value)


def test_pause_samples_stay_within_bounds_and_cluster_around_center():
    pauses = Pauses(0.2, 1.0, 0.5)
    rng = random.Random(1234)
    samples = [pauses.sample(rng) for _ in range(5000)]
    assert all(0.2 <= sample <= 1.0 for sample in samples)
    assert abs(sum(samples) / len(samples) - 0.5) < 0.05
    assert len(set(samples)) > 100


def test_find_segments_filters_and_sorts(tmp_path):
    for name in ["00002.mp3", "00001.mp3", "podcast.mp3", "notes.txt", "00010.mp3", "1.mp3", "00003-x.mp3"]:
        (tmp_path / name).write_bytes(b"")
    assert [path.name for path in find_segments(tmp_path)] == ["00001.mp3", "00002.mp3", "00010.mp3"]


def test_find_segments_requires_files(tmp_path):
    with pytest.raises(CompileError, match="no segment files"):
        find_segments(tmp_path)


def test_compile_merges_with_pauses(tmp_path):
    tone(tmp_path / "00001.mp3", 300)
    tone(tmp_path / "00002.mp3", 300)
    tone(tmp_path / "00003.mp3", 300)

    output = compile_podcast(tmp_path, tmp_path / "out" / "episode.mp3", Pauses(0.5, 0.5, 0.5), rng=random.Random(0))

    assert output == tmp_path / "out" / "episode.mp3"
    duration = len(AudioSegment.from_mp3(output))
    # 3 x 300 ms audio + 2 x 500 ms silence, allowing for MP3 frame padding.
    assert 1850 <= duration <= 2050
