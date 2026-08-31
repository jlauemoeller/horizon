FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY horizon ./horizon
COPY tests ./tests
RUN pip install --no-cache-dir ".[test]"

# The host directory is mounted here; script and working-directory paths are resolved against it.
WORKDIR /work
ENTRYPOINT ["horizon"]
