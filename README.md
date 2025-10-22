# docker-srt-folders

`docker-srt-folders` is a lightweight web application and CLI for generating `.srt` subtitle
files from audio or video collections. It wraps the
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) engine in a Docker image so
you can mount media folders (local or remote) and create subtitles with a couple of clicks.

---

## Features

- ✅ **Browser-based workflow** – select one or more folders to scan and decide whether to
  process them recursively.
- ✅ **Automatic subtitle generation** – uses `faster-whisper` to create `.srt` files next to
  the original media.
- ✅ **Docker ready** – designed to run inside a container with media folders mounted from your
  local machine or a network share.
- ✅ **Command line helper** – run the same workflow from a terminal with `subtitle_cli.py`.

---

## Prerequisites

- Docker (20.10+) for running the container.
- Optional: Python 3.11 if you want to run the application directly on your host machine.

The container installs `ffmpeg`, which is required by `faster-whisper` to decode media
streams.

---

## Quick start with Docker

1. Build the image:

   ```bash
   docker build -t docker-srt-folders .
   ```

2. Run the container. Mount the directories that contain your media files into `/data`
   (or another path – see [Environment variables](#environment-variables)):

   ```bash
   docker run \
     --rm \
     -p 8000:8000 \
     -v /path/to/local/media:/data/media \
     docker-srt-folders
   ```

3. Open <http://localhost:8000>. The web interface lists the mounted directories so you can
   select them for transcription.

---

## Using the web interface

1. Visit the home page and tick the folders you want to scan. Use the "Extra folder path"
   field to add a custom path (for example, an SMB share mounted in the container).
2. Choose whether to scan sub-folders recursively and whether to overwrite existing `.srt`
   files.
3. Click **Create subtitles**. The results table will show the status for every processed
   media file.

Subtitles are written next to the source file. For example, `movie.mp4` becomes
`movie.srt`.

---

## Command line usage

You can perform the same operation without the web UI:

```bash
python subtitle_cli.py /data/media /network/videos --overwrite
```

Use `--help` to see all available options such as disabling recursion or forcing a model
size.

---

## Running without Docker

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start the development server:

   ```bash
   flask --app app.web:create_app run --host 0.0.0.0 --port 8000
   ```

3. Mount or symlink your media directories into the folder pointed to by
   `SUBTITLE_BASE_DIR` (default: `/data`).

---

## Environment variables

The following variables are read by both the web app and the CLI:

| Variable | Default | Description |
|----------|---------|-------------|
| `SUBTITLE_BASE_DIR` | `/data` | Root folder containing media directories exposed in the UI. |
| `SUBTITLE_MODEL_SIZE` | `small` | Whisper model size to load (e.g. `base`, `medium`, `large`). |
| `SUBTITLE_COMPUTE_TYPE` | `int8_float16` | Controls inference precision. |
| `SUBTITLE_LANGUAGE` | _auto_ | Force transcription to a specific language code (e.g. `en`). |
| `SUBTITLE_BEAM_SIZE` | _unset_ | Override the decoding beam size. |
| `SUBTITLE_VAD_FILTER` | `true` | Enable voice activity detection to trim silence. |
| `FLASK_SECRET_KEY` | `docker-srt-folders` | Secret key for session cookies used by flash messages. |

---

## Repository layout

```
app/
├── __init__.py        # Flask application factory
├── transcription.py   # Subtitle generation helpers
├── templates/
│   └── index.html     # Single page web interface
subtitle_cli.py        # Command line interface
Dockerfile             # Container definition
requirements.txt       # Python dependencies
README.md              # This manual
```

---

## Troubleshooting

- **No folders appear in the list.** Ensure the media directory is mounted into the
  container and that the path matches `SUBTITLE_BASE_DIR`.
- **Transcription fails for some files.** Check the container logs. A common cause is
  unsupported or corrupted media formats. Re-run with the `--overwrite` flag after fixing
  the underlying issue.
- **Model downloads are slow.** The first run downloads the Whisper model. Subsequent runs
  reuse the cached weights located in `/root/.cache/huggingface` inside the container.

Happy transcribing! 🎬
