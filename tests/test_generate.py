import pytest

from horizon.generate import GenerateError, generate, segment_filename
from horizon.script import Line


def fake_synthesize(inputs):
    return "|".join(f"{voice_id}:{text}" for text, voice_id in inputs).encode()


def test_segment_filename_format():
    assert segment_filename(1) == "00001.mp3"
    assert segment_filename(123) == "00123.mp3"


def test_generate_packs_lines_into_segments(tmp_path):
    lines = [Line("linda", "Hello."), Line("carl", "Hi."), Line("linda", "Bye.")]
    target = tmp_path / "out" / "nested"

    written = generate(lines, {"linda": "v-linda", "carl": "v-carl"}, target, synthesize=fake_synthesize)

    assert [path.name for path in written] == ["00001.mp3"]
    assert (target / "00001.mp3").read_bytes() == b"v-linda:Hello.|v-carl:Hi.|v-linda:Bye."


def test_generate_respects_character_limit(tmp_path):
    lines = [Line("linda", "a" * 6), Line("carl", "b" * 5), Line("linda", "c" * 4)]
    written = generate(lines, {"linda": "L", "carl": "C"}, tmp_path, synthesize=fake_synthesize, limit=10)
    assert [path.name for path in written] == ["00001.mp3", "00002.mp3"]
    assert (tmp_path / "00001.mp3").read_bytes() == b"L:aaaaaa"
    assert (tmp_path / "00002.mp3").read_bytes() == b"C:bbbbb|L:cccc"


def test_generate_overwrites_existing_files(tmp_path):
    (tmp_path / "00001.mp3").write_bytes(b"old")
    generate([Line("linda", "New.")], {"linda": "v"}, tmp_path, synthesize=fake_synthesize)
    assert (tmp_path / "00001.mp3").read_bytes() == b"v:New."


def test_missing_voice_is_an_error_before_any_call(tmp_path):
    calls = []

    def recording(inputs):
        calls.append(inputs)
        return b""

    lines = [Line("linda", "Hello."), Line("carl", "Hi."), Line("zed", "Yo.")]
    with pytest.raises(GenerateError, match="carl, zed"):
        generate(lines, {"linda": "v"}, tmp_path, synthesize=recording)
    assert calls == []


def test_missing_api_key_is_an_error(monkeypatch):
    from horizon.generate import elevenlabs_synthesize

    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    with pytest.raises(GenerateError, match="ELEVENLABS_API_KEY"):
        elevenlabs_synthesize([("hi", "voice")])
