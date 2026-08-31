import json
import random

import pytest

from horizon.script import Line
from horizon.writer import (
    HOSTS,
    PROMPT_PATH,
    Script,
    WriterError,
    choose_expert,
    episode_basename,
    parse_script,
    render_prompt,
    slugify,
    write_script,
)

RAW = json.dumps(
    {
        "title": "Why Glass Bends",
        "lines": [
            {"speaker": "Linda", "text": "Carl, a confession.\n"},
            {"speaker": "Carl", "text": "[laughs]  Go on."},
            {"speaker": "Linda", "text": "   "},
        ],
    }
)


def test_prompt_file_has_both_markers():
    template = PROMPT_PATH.read_text()
    assert "${speaker}" in template and "${subject}" in template
    rendered = render_prompt("Foldable screens", "Carl", template)
    assert "The expert role for this episode is played by: Carl" in rendered
    assert "The subject for this episode is: Foldable screens" in rendered
    assert "$" not in rendered


def test_choose_expert_is_random_between_hosts():
    picks = {choose_expert(random.Random(seed)) for seed in range(50)}
    assert picks == set(HOSTS)


def test_parse_script_normalises_lines_and_drops_empty_ones():
    script = parse_script(RAW, "Glass", "Carl")
    assert script.title == "Why Glass Bends"
    assert script.expert == "Carl"
    assert script.lines == [Line("linda", "Carl, a confession."), Line("carl", "[laughs] Go on.")]


@pytest.mark.parametrize(
    "raw, message",
    [
        ("not json", "valid JSON"),
        ('{"title": "x"}', "missing"),
        ('{"title": "", "lines": []}', "empty episode title"),
        ('{"title": "x", "lines": [{"speaker": "Bob", "text": "hi"}]}', "unknown speaker"),
        ('{"title": "x", "lines": [{"speaker": "Carl"}]}', "line 1"),
        ('{"title": "x", "lines": []}', "without any dialogue"),
    ],
)
def test_parse_script_errors(raw, message):
    with pytest.raises(WriterError, match=message):
        parse_script(raw, "s", "Carl")


def test_write_script_renders_prompt_and_parses_answer():
    prompts = []

    def fake(prompt):
        prompts.append(prompt)
        return RAW

    script = write_script("Glass", "Linda", write=fake)
    assert "played by: Linda" in prompts[0]
    assert script.subject == "Glass"


def test_json_and_markdown_rendering():
    script = Script("Why Glass Bends", "Glass", "Carl", [Line("linda", "Hi."), Line("carl", "Hello.")])
    data = json.loads(script.to_json())
    assert data == {
        "title": "Why Glass Bends",
        "subject": "Glass",
        "expert": "Carl",
        "lines": [{"speaker": "Linda", "text": "Hi."}, {"speaker": "Carl", "text": "Hello."}],
    }
    markdown = script.to_markdown()
    assert '## Episode: "Why Glass Bends"' in markdown
    assert "Carl (expert) & Linda" in markdown
    assert markdown.split("---\n")[1].strip() == "**LINDA:** Hi.\n\n**CARL:** Hello."


def test_slugify_and_basename():
    assert slugify("Why Glass Bends: The Science!") == "why_glass_bends_the_science"
    assert slugify("  Ünïcode & symbols ") == "n_code_symbols"
    assert slugify("!!!") == "untitled"
    assert episode_basename("Why Glass Bends") == "why_glass_bends"
    assert episode_basename("Why Glass Bends", 12) == "12_why_glass_bends"


def test_missing_api_key_is_an_error(monkeypatch):
    from horizon.writer import anthropic_write

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(WriterError, match="ANTHROPIC_API_KEY"):
        anthropic_write("prompt")
