"""Flask web interface for the docker-srt-folders application."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from flask import Flask, flash, redirect, render_template, request, url_for

from .transcription import SubtitleGenerator, TranscriptionResult


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "docker-srt-folders")

    base_directory = Path(os.environ.get("SUBTITLE_BASE_DIR", "/data")).expanduser()
    model_size = os.environ.get("SUBTITLE_MODEL_SIZE", "small")
    compute_type = os.environ.get("SUBTITLE_COMPUTE_TYPE", "int8_float16")
    language = os.environ.get("SUBTITLE_LANGUAGE") or None
    beam_size = _safe_int(os.environ.get("SUBTITLE_BEAM_SIZE"))
    vad_filter = _env_flag(os.environ.get("SUBTITLE_VAD_FILTER", "true"))

    subtitle_generator = SubtitleGenerator(
        model_size=model_size,
        compute_type=compute_type,
        language=language,
        beam_size=beam_size,
        vad_filter=vad_filter,
    )

    @app.route("/", methods=["GET", "POST"])
    def index():
        directories = _discover_directories(base_directory)
        results: List[TranscriptionResult] | None = None

        if request.method == "POST":
            selected = request.form.getlist("directories")
            recursive = bool(request.form.get("recursive"))
            overwrite = bool(request.form.get("overwrite"))
            extra_path = request.form.get("extra_path")

            if extra_path:
                selected.append(extra_path)

            if not selected:
                flash("Select at least one directory to process.", "warning")
                return redirect(url_for("index"))

            missing = [path for path in selected if not Path(path).expanduser().exists()]
            if missing:
                flash(
                    f"The following paths do not exist: {', '.join(missing)}",
                    "danger",
                )
            else:
                results = subtitle_generator.transcribe_directories(
                    selected,
                    recursive=recursive,
                    overwrite=overwrite,
                    skip_existing=not overwrite,
                )

        return render_template(
            "index.html",
            available_directories=directories,
            base_directory=base_directory,
            results=results,
        )

    return app


def _discover_directories(base_directory: Path) -> List[Path]:
    base_directory.mkdir(parents=True, exist_ok=True)
    directories: List[Path] = []

    for entry in base_directory.iterdir():
        if entry.is_dir():
            directories.append(entry)

    directories.sort()
    return directories


def _env_flag(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _safe_int(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
