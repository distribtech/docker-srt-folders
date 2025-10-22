"""Utilities for generating subtitles with faster-whisper."""
from __future__ import annotations

import itertools
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from faster_whisper import WhisperModel

# Common set of audio and video containers that faster-whisper can process.
MEDIA_EXTENSIONS = {
    ".aac",
    ".aiff",
    ".flac",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".wav",
    ".webm",
    ".wma",
}


@dataclass
class TranscriptionResult:
    """Outcome of generating subtitles for a single media file."""

    source: Path
    output: Path | None
    created: bool
    message: str


class SubtitleGenerator:
    """Generate subtitle files for media collections.

    Parameters are intentionally explicit so that the object can be reused between
    requests (e.g. for HTTP handlers or CLIs).
    """

    def __init__(
        self,
        model_size: str = "small",
        compute_type: str = "int8_float16",
        language: str | None = None,
        beam_size: int | None = None,
        vad_filter: bool = True,
    ) -> None:
        self.model_size = model_size
        self.compute_type = compute_type
        self.language = language
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        self._model: WhisperModel | None = None

    def _ensure_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(self.model_size, compute_type=self.compute_type)
        return self._model

    def transcribe_directories(
        self,
        directories: Sequence[os.PathLike[str] | str],
        recursive: bool = True,
        overwrite: bool = False,
        skip_existing: bool = True,
    ) -> List[TranscriptionResult]:
        """Generate subtitles for every media file in ``directories``.

        Parameters
        ----------
        directories:
            Iterable of paths that should be scanned for media files.
        recursive:
            Whether to traverse sub-directories.
        overwrite:
            When ``True`` the existing subtitle file is replaced.
        skip_existing:
            When ``True`` files that already have subtitles are skipped.
        """

        expanded_directories = [Path(path).expanduser() for path in directories]
        media_files = list(
            itertools.chain.from_iterable(
                _iter_media_files(directory, recursive=recursive)
                for directory in expanded_directories
            )
        )

        if not media_files:
            return [
                TranscriptionResult(
                    source=Path(directory),
                    output=None,
                    created=False,
                    message="No media files detected.",
                )
                for directory in expanded_directories
            ]

        model = self._ensure_model()
        results: List[TranscriptionResult] = []

        for media_file in media_files:
            output_file = media_file.with_suffix(".srt")
            if output_file.exists():
                if overwrite:
                    output_file.unlink()
                elif skip_existing:
                    results.append(
                        TranscriptionResult(
                            source=media_file,
                            output=output_file,
                            created=False,
                            message="Subtitle already exists.",
                        )
                    )
                    continue

            try:
                segments, _ = model.transcribe(
                    str(media_file),
                    language=self.language,
                    beam_size=self.beam_size,
                    vad_filter=self.vad_filter,
                )
                _write_srt(segments, output_file)
                results.append(
                    TranscriptionResult(
                        source=media_file,
                        output=output_file,
                        created=True,
                        message="Subtitle created successfully.",
                    )
                )
            except Exception as exc:  # pragma: no cover - bubble up error information
                results.append(
                    TranscriptionResult(
                        source=media_file,
                        output=None,
                        created=False,
                        message=f"Failed to generate subtitle: {exc}",
                    )
                )

        return results


def _iter_media_files(directory: Path, recursive: bool = True) -> Iterable[Path]:
    """Yield media files contained in ``directory`` respecting ``recursive``."""
    if not directory.exists():
        return

    if recursive:
        for root, _, files in os.walk(directory):
            for name in files:
                path = Path(root) / name
                if path.suffix.lower() in MEDIA_EXTENSIONS:
                    yield path
    else:
        for entry in directory.iterdir():
            if entry.is_file() and entry.suffix.lower() in MEDIA_EXTENSIONS:
                yield entry


def _write_srt(segments: Iterable, destination: Path) -> None:
    """Persist segments from faster-whisper into the ``destination`` file."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = []

    for index, segment in enumerate(segments, start=1):
        start_time = _format_timestamp(segment.start)
        end_time = _format_timestamp(segment.end)
        text = segment.text.strip().replace(" --> ", " → ")
        lines.append(f"{index}\n{start_time} --> {end_time}\n{text}\n")

    destination.write_text("\n".join(lines), encoding="utf-8")


def _format_timestamp(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
