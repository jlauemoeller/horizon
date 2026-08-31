# horizon

Command line podcast generator for the "Horizon" podcast. Give it a subject; Claude writes the
episode script (with web research), ElevenLabs voices it with the text-to-dialogue API, and the
result is one MP3 plus the script. Everything runs inside a Docker container; only Docker is
needed on the host.

## Examples

Some sample output is available in the `episodes` folder.

## Usage

```sh
export ANTHROPIC_API_KEY=...
export ELEVENLABS_API_KEY=...

./horizon.sh --subject="How foldable phone screens work" --episode=12 --pauses=0.2:1.0:0.5
```

Without `--subject`, the subject is read from standard input until EOF, so a longer brief can be
piped in:

```sh
./horizon.sh --episode=13 < brief.txt
```

This produces, in `episodes/` (override with `--output-directory=PATH`):

- `12_<title>.mp3` – the finished episode
- `12_<title>.json` – the script as returned by Claude (title, subject, expert, lines)
- `12_<title>.md` – the same script rendered as Markdown

`<title>` is the episode title chosen by Claude, lower-cased with underscores for anything
that is not a letter or digit. `--episode` is optional; without it the prefix is omitted.
`--output-directory` defaults to `episodes` and must be relative to where you run
`horizon.sh` (the current directory is mounted into the container).

Which of Carl and Linda plays the subject matter expert is chosen at random for every episode
unless you pin it with `--expert=carl` or `--expert=linda`. The choice is recorded in the
script files.

Carl and Linda are voiced by the ElevenLabs voices `UgBBYS2sOqTuMpoF3BR0` and
`OZxMHsGaBmV5pjMIDIn0` respectively; override either with `--voice-carl=VOICE_ID` or
`--voice-linda=VOICE_ID`.

`--pauses=lower:upper:center` (optional) controls the silence inserted between dialogue segments
(seconds), drawn from a normal distribution centred on `center` and clipped to
`[lower, upper]`. Within a segment the flow between speakers is produced by the
ElevenLabs model itself; the pauses only apply between segments.

## How it works

The script uses a simple pipeline architecture with the following stages:

1. **Write** – `horizon/prompt.md` is filled in with the subject and the expert's name and
   sent to `claude-opus-5` (adaptive thinking, effort `xhigh`, web search enabled with at most
   20 searches). The answer is constrained to a JSON schema with `title` and `lines[{speaker, text}]`.
2. **Generate** – consecutive lines are packed into segments of at most 2000 characters (the
   ElevenLabs limit per request; longer lines are split one sentence at a time) and each
   segment is sent to the text-to-dialogue API. Segment MP3s live in a temporary directory
   that is removed when the program exits.
3. **Compile** – the segments are merged in order with random pauses in between.

## Tests

```sh
./horizon.sh test      # run the unit tests inside the container
./horizon.sh build     # rebuild the image after changing the code
```

Tests never call the Anthropic or ElevenLabs APIs.

The Docker image is built automatically on first use and can be renamed via the
`HORIZON_IMAGE` environment variable (default `horizon:latest`).
