import io
from pathlib import Path

import pytest

from horizon.cli import DEFAULT_VOICES, UsageError, main, parse_args, read_subject
from horizon.compile import Pauses


def test_parse_full_command_line():
    options = parse_args(
        ["--subject=Foldable screens", "--voice-Carl=7283", "--voice-LINDA=9034", "--episode=12",
         "--output-directory=episodes", "--pauses=0.1:2:1"]
    )
    assert options.subject == "Foldable screens"
    assert options.voices == {"carl": "7283", "linda": "9034"}
    assert options.episode == 12
    assert options.output_directory == Path("episodes")
    assert options.pauses == Pauses(0.1, 2.0, 1.0)


def test_defaults():
    options = parse_args(["--subject=x"])
    assert options.subject == "x"
    assert options.episode is None
    assert options.voices == {"carl": "UgBBYS2sOqTuMpoF3BR0", "linda": "OZxMHsGaBmV5pjMIDIn0"}
    assert options.output_directory == Path("episodes")
    assert options.pauses == Pauses(0.2, 1.0, 0.5)


def test_voice_option_overrides_one_default():
    options = parse_args(["--subject=x", "--voice-carl=1"])
    assert options.voices == {"carl": "1", "linda": DEFAULT_VOICES["linda"]}
    assert DEFAULT_VOICES["carl"] == "UgBBYS2sOqTuMpoF3BR0"  # defaults are not mutated


@pytest.mark.parametrize(
    "argv, message",
    [
        (["--help"], "^$"),
        (["--subject=x", "--voice-carl=1", "--episode=abc"], "--episode must be"),
        (["--subject=x", "--voice-carl=1", "--bogus=1"], "unknown option"),
        (["--subject=x", "--voice-carl=1", "--pauses"], "form --name=value"),
        (["--subject=", "--voice-carl=1"], "requires a value"),
    ],
)
def test_parse_errors(argv, message):
    with pytest.raises(UsageError, match=message):
        parse_args(argv)


def test_main_usage_error_exit_code(capsys):
    assert main(["--bogus=1"]) == 2
    assert "unknown option" in capsys.readouterr().err


def test_main_help(capsys):
    assert main(["--help"]) == 0
    assert "Usage:" in capsys.readouterr().err


def test_main_without_arguments_on_a_terminal_prints_usage(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO())
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    assert main([]) == 0
    assert "Usage:" in capsys.readouterr().err


def test_subject_is_read_from_stdin_when_not_given(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("sys.stdin", io.StringIO("  Why glass bends\n"))
    assert main([]) == 1  # got past argument parsing, failed on the missing API key
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err


def test_read_subject_strips_and_joins_lines():
    assert read_subject(io.StringIO("  Why glass bends\nand how it breaks\n\n")) == "Why glass bends\nand how it breaks"


def test_read_subject_rejects_empty_stdin(monkeypatch, capsys):
    with pytest.raises(UsageError, match="nothing was read from stdin"):
        read_subject(io.StringIO("  \n"))
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert main([]) == 2
    assert "nothing was read from stdin" in capsys.readouterr().err


def test_main_reports_missing_anthropic_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    code = main(["--subject=x", "--voice-carl=1", "--voice-linda=2", f"--output-directory={tmp_path}"])
    assert code == 1
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err


def test_parse_expert():
    assert parse_args(["--subject=x", "--voice-carl=1", "--expert=carl"]).expert == "Carl"
    assert parse_args(["--subject=x", "--voice-carl=1", "--expert=LINDA"]).expert == "Linda"
    assert parse_args(["--subject=x", "--voice-carl=1"]).expert is None


def test_parse_expert_rejects_unknown_host():
    with pytest.raises(UsageError, match="--expert must be one of carl, linda"):
        parse_args(["--subject=x", "--voice-carl=1", "--expert=bob"])
