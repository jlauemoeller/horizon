#!/usr/bin/env bash
# Runs horizon inside its Docker container.
#
#   ./horizon.sh --subject="Foldable screens" --episode=1 [--voice-carl=ID --voice-linda=ID]
#   ./horizon.sh --episode=2 < brief.txt   # subject read from stdin when --subject is omitted
#   ./horizon.sh test          # run the unit tests inside the container
#   ./horizon.sh build         # (re)build the image
#
# The current directory is mounted into the container at /work, so
# --output-directory (default: episodes) must be relative to the directory you run this from.
# ANTHROPIC_API_KEY and ELEVENLABS_API_KEY are passed through from your environment.

set -euo pipefail

IMAGE="${HORIZON_IMAGE:-horizon:latest}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

build_image() {
    docker build -t "$IMAGE" "$SCRIPT_DIR"
}

if [[ "${1:-}" == "build" ]]; then
    build_image
    exit 0
fi

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "horizon: building Docker image $IMAGE" >&2
    build_image
fi

if [[ "${1:-}" == "test" ]]; then
    shift
    exec docker run --rm --entrypoint pytest -w /app "$IMAGE" "$@"
fi

for arg in "$@"; do
    case "$arg" in
        --output-directory=/*)
            echo "horizon: paths must be relative to the current directory (got $arg)" >&2
            exit 2 ;;
        --output-directory=..*)
            echo "horizon: paths must not leave the current directory (got $arg)" >&2
            exit 2 ;;
    esac
done

# -t only when stdin is a terminal: lets a bare `horizon.sh` print usage instead of waiting on stdin.
exec docker run --rm -i $([ -t 0 ] && echo -t) \
    --user "$(id -u):$(id -g)" \
    -e "ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY:-}" \
    -e "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}" \
    -v "$PWD:/work" \
    "$IMAGE" "$@"
