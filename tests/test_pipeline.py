import json
import random
from pathlib import Path

import pytest
from pydub import AudioSegment
from pydub.generators import Sine

from horizon.compile import Pauses
from horizon.generate import GenerateError
from horizon.pipeline import run

RAW = json.dumps(
    {"title": "Why Glass Bends", "lines": [{"speaker": "Linda", "text": "Hi."}, {"speaker": "Carl", "text": "Hello."}]}
)


def tone_synthesizer(inputs):
    from io import BytesIO

    buffer = BytesIO()
    Sine(440).to_audio_segment(duration=300 * len(inputs)).export(buffer, format="mp3")
    return buffer.getvalue()


def test_run_writes_episode_and_scripts_and_cleans_up_segments(tmp_path, monkeypatch):
    temp_root = tmp_path / "tmp"
    temp_root.mkdir()
    monkeypatch.setenv("TMPDIR", str(temp_root))
    import tempfile

    tempfile.tempdir = None  # make tempfile re-read TMPDIR
    output = tmp_path / "out"

    episode = run(
        "Glass",
        {"carl": "C", "linda": "L"},
        output,
        episode=7,
        pauses=Pauses(0.5, 0.5, 0.5),
        write=lambda prompt: RAW,
        synthesize=tone_synthesizer,
        rng=random.Random(0),
    )

    assert episode.mp3 == output / "7_why_glass_bends.mp3"
    assert episode.script_json == output / "7_why_glass_bends.json"
    assert episode.script_markdown == output / "7_why_glass_bends.md"
    assert json.loads(episode.script_json.read_text())["title"] == "Why Glass Bends"
    assert "**LINDA:** Hi." in episode.script_markdown.read_text()
    assert 500 <= len(AudioSegment.from_mp3(episode.mp3)) <= 800
    assert sorted(path.name for path in output.iterdir()) == [
        "7_why_glass_bends.json",
        "7_why_glass_bends.md",
        "7_why_glass_bends.mp3",
    ]
    assert list(temp_root.iterdir()) == []  # segment files were temporary
    tempfile.tempdir = None


def test_run_without_episode_number(tmp_path):
    episode = run("Glass", {"carl": "C", "linda": "L"}, tmp_path, write=lambda p: RAW, synthesize=tone_synthesizer)
    assert episode.mp3.name == "why_glass_bends.mp3"


def test_run_requires_voices_for_all_speakers(tmp_path):
    calls = []

    def recording(inputs):
        calls.append(inputs)
        return b""

    with pytest.raises(GenerateError, match="carl"):
        run("Glass", {"linda": "L"}, tmp_path, write=lambda p: RAW, synthesize=recording)
    assert calls == []
    assert not (tmp_path / "why_glass_bends.json").exists()


def test_run_uses_requested_expert(tmp_path):
    prompts = []

    def fake_write(prompt):
        prompts.append(prompt)
        return RAW

    run("Glass", {"carl": "C", "linda": "L"}, tmp_path, expert="Linda", write=fake_write, synthesize=tone_synthesizer)
    assert "played by: Linda" in prompts[0]
    assert json.loads((tmp_path / "why_glass_bends.json").read_text())["expert"] == "Linda"
