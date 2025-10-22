"""Command line helper for docker-srt-folders."""
from __future__ import annotations

import argparse
import os

from app.transcription import SubtitleGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate subtitles using faster-whisper")
    parser.add_argument(
        "directories",
        nargs="+",
        help="One or more directories to scan for media files.",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        default=True,
        help="Disable recursive scanning.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing subtitle files.",
    )
    parser.add_argument(
        "--model-size",
        default=os.environ.get("SUBTITLE_MODEL_SIZE", "small"),
        help="Whisper model size to use (default: %(default)s).",
    )
    parser.add_argument(
        "--compute-type",
        default=os.environ.get("SUBTITLE_COMPUTE_TYPE", "int8_float16"),
        help="Compute type to use for faster-whisper (default: %(default)s).",
    )
    parser.add_argument(
        "--language",
        default=os.environ.get("SUBTITLE_LANGUAGE"),
        help="Force a specific transcription language (default: auto-detect).",
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        default=_env_int("SUBTITLE_BEAM_SIZE"),
        help="Override beam size for decoding.",
    )
    parser.add_argument(
        "--no-vad",
        dest="vad_filter",
        action="store_false",
        default=os.environ.get("SUBTITLE_VAD_FILTER", "true").lower() in {"1", "true", "yes", "on"},
        help="Disable voice activity detection.",
    )
    return parser.parse_args()


def _env_int(name: str) -> int | None:
    value = os.environ.get(name)
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def main() -> None:
    args = parse_args()
    generator = SubtitleGenerator(
        model_size=args.model_size,
        compute_type=args.compute_type,
        language=args.language,
        beam_size=args.beam_size,
        vad_filter=args.vad_filter,
    )
    results = generator.transcribe_directories(
        args.directories,
        recursive=args.recursive,
        overwrite=args.overwrite,
        skip_existing=not args.overwrite,
    )
    for result in results:
        status = "created" if result.created else "skipped"
        print(f"{result.source} -> {result.output or 'n/a'} ({status}) {result.message}")


if __name__ == "__main__":
    main()
