"""Step 0: write the podcast script with the Anthropic API."""

import json
import os
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Callable

from .script import Line, normalise_speaker

PROMPT_PATH = Path(__file__).with_name("prompt.md")
HOSTS = ("Carl", "Linda")
PODCAST_NAME = "Horizon"

MODEL = "claude-opus-5"
EFFORT = "xhigh"
MAX_TOKENS = 64000
MAX_WEB_SEARCHES = 20
API_KEY_ENV = "ANTHROPIC_API_KEY"

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Short episode title, without the podcast name"},
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "speaker": {"type": "string", "enum": list(HOSTS)},
                    "text": {"type": "string"},
                },
                "required": ["speaker", "text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "lines"],
    "additionalProperties": False,
}

# A writer takes the rendered prompt and returns the model's JSON text.
Writer = Callable[[str], str]


class WriterError(Exception):
    pass


@dataclass(frozen=True)
class Script:
    title: str
    subject: str
    expert: str
    lines: list[Line] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "title": self.title,
                "subject": self.subject,
                "expert": self.expert,
                "lines": [{"speaker": line.speaker.capitalize(), "text": line.text} for line in self.lines],
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n"

    def to_markdown(self) -> str:
        clarifier = next(host for host in HOSTS if host != self.expert)
        header = [
            f"# {PODCAST_NAME}",
            "",
            f'## Episode: "{self.title}"',
            "",
            f"### Subject: {self.subject}",
            "",
            f"### Hosts: {self.expert} (expert) & {clarifier} (clarifying questions)",
            "",
            "---",
            "",
        ]
        body = [f"**{line.speaker.upper()}:** {line.text}\n" for line in self.lines]
        return "\n".join(header + body)


def choose_expert(rng: random.Random | None = None) -> str:
    return (rng or random.Random()).choice(HOSTS)


def render_prompt(subject: str, expert: str, template: str | None = None) -> str:
    template = template if template is not None else PROMPT_PATH.read_text(encoding="utf-8")
    return Template(template).substitute(speaker=expert, subject=subject)


def parse_script(raw: str, subject: str, expert: str) -> Script:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise WriterError(f"the model did not return valid JSON: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("title"), str) or not isinstance(data.get("lines"), list):
        raise WriterError("the model's JSON is missing 'title' or 'lines'")
    title = data["title"].strip()
    if not title:
        raise WriterError("the model returned an empty episode title")

    lines: list[Line] = []
    for index, item in enumerate(data["lines"], start=1):
        if not isinstance(item, dict) or not isinstance(item.get("speaker"), str) or not isinstance(item.get("text"), str):
            raise WriterError(f"script line {index} is not an object with 'speaker' and 'text'")
        speaker = normalise_speaker(item["speaker"])
        text = " ".join(item["text"].split())
        if speaker not in {host.lower() for host in HOSTS}:
            raise WriterError(f"script line {index} has unknown speaker {item['speaker']!r}")
        if text:
            lines.append(Line(speaker, text))
    if not lines:
        raise WriterError("the model returned a script without any dialogue lines")
    return Script(title=title, subject=subject, expert=expert, lines=lines)


def anthropic_write(prompt: str, log: Callable[[str], None] = lambda message: None) -> str:
    """Ask Claude for the script. Returns the JSON text of the final answer."""
    if not os.environ.get(API_KEY_ENV):
        raise WriterError(f"{API_KEY_ENV} is not set in the environment")

    import anthropic

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": prompt}]
    request = dict(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": SCRIPT_SCHEMA}},
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": MAX_WEB_SEARCHES}],
    )
    try:
        # The model may pause between web searches (stop_reason "pause_turn"); resume until it finishes.
        for _ in range(10):
            with client.messages.stream(messages=messages, **request) as stream:
                for event in stream:
                    if event.type == "content_block_start" and event.content_block.type == "server_tool_use":
                        log("  searching the web...")
                response = stream.get_final_message()
            if response.stop_reason != "pause_turn":
                break
            messages.append({"role": "assistant", "content": response.content})
        else:
            raise WriterError("the model kept pausing without finishing the script")
    except anthropic.AuthenticationError as error:
        raise WriterError(f"Anthropic API rejected the API key: {error.message}") from error
    except anthropic.APIStatusError as error:
        raise WriterError(f"Anthropic API returned {error.status_code}: {error.message}") from error
    except anthropic.APIConnectionError as error:
        raise WriterError(f"could not reach the Anthropic API: {error}") from error

    if response.stop_reason == "refusal":
        detail = response.stop_details.explanation if response.stop_details else ""
        raise WriterError(f"the model declined to write this script: {detail}")
    if response.stop_reason == "max_tokens":
        raise WriterError("the model ran out of output tokens before finishing the script")
    log(f"  tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
    return "".join(block.text for block in response.content if block.type == "text")


def write_script(
    subject: str,
    expert: str,
    write: Writer = anthropic_write,
    log: Callable[[str], None] = lambda message: None,
) -> Script:
    return parse_script(write(render_prompt(subject, expert)), subject, expert)


_UNSAFE_RE = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """Lower-case file name stem with underscores instead of spaces and punctuation."""
    slug = _UNSAFE_RE.sub("_", title.lower()).strip("_")
    return slug or "untitled"


def episode_basename(title: str, episode: int | None = None) -> str:
    slug = slugify(title)
    return f"{episode}_{slug}" if episode is not None else slug
