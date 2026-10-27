#!/usr/bin/env python3
"""Separate spoken voice from a mixed lesson recording using UVR models.

The command delegates source separation to the ``audio-separator`` CLI,
which exposes models from the Ultimate Vocal Remover ecosystem.  It then
normalizes the extracted voice for speech recognition and writes a manifest
with the generated files and warnings.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_MODEL = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
VOICE_TOKENS = ("vocals", "vocal", "voice", "voz", "speech")
ACCOMPANIMENT_TOKENS = (
    "instrumental",
    "accompaniment",
    "other",
    "drums",
    "instrument",
    "music",
)
SUPPORTED_AUDIO_SUFFIXES = {
    ".wav",
    ".mp3",
    ".flac",
    ".m4a",
    ".ogg",
    ".opus",
    ".aac",
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
}


class SeparationError(RuntimeError):
    """Raise when a required tool or output is unavailable."""


def executable(name: str) -> str | None:
    """Return the executable path when available."""

    return shutil.which(name)


def run(command: list[str], *, dry_run: bool = False) -> subprocess.CompletedProcess[str] | None:
    """Print and execute a command, preserving paths with spaces safely."""

    print("$", " ".join(quote_for_display(item) for item in command))
    if dry_run:
        return None
    return subprocess.run(command, check=True, text=True, capture_output=True)


def quote_for_display(value: str) -> str:
    """Quote a command argument for readable logs without shell execution."""

    if value and all(char.isalnum() or char in "._/-:" for char in value):
        return value
    return repr(value)


def find_outputs(directory: Path, before: set[Path]) -> list[Path]:
    """Find newly generated audio files, excluding the input file."""

    outputs = []
    for path in directory.rglob("*"):
        if not path.is_file() or path in before:
            continue
        if path.suffix.lower() in {".wav", ".flac", ".mp3", ".m4a", ".ogg"}:
            outputs.append(path)
    return sorted(outputs, key=lambda item: item.stat().st_mtime)


def choose_stem(files: Iterable[Path], tokens: tuple[str, ...]) -> Path | None:
    """Choose a generated stem based on filename tokens."""

    ranked: list[tuple[int, Path]] = []
    for path in files:
        name = path.stem.lower()
        score = sum(1 for token in tokens if token in name)
        if score:
            ranked.append((score, path))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1].stat().st_mtime), reverse=True)
    return ranked[0][1]


def unique_target(path: Path, overwrite: bool) -> Path:
    """Return a safe target path without overwriting by default."""

    if overwrite or not path.exists():
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def copy_as(source: Path, target: Path, overwrite: bool) -> Path:
    """Copy a generated stem to a predictable output name."""

    destination = unique_target(target, overwrite)
    shutil.copy2(source, destination)
    return destination


def normalize_voice(ffmpeg: str, source: Path, target: Path, dry_run: bool) -> None:
    """Create a mono 16 kHz PCM voice file for speech services."""

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(target),
    ]
    run(command, dry_run=dry_run)


def write_manifest(path: Path, data: dict) -> None:
    """Write UTF-8 metadata for reproducibility."""

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Separar voz falada e acompanhamento usando modelos UVR via audio-separator."
    )
    parser.add_argument("input", type=Path, help="Arquivo de áudio ou vídeo de entrada.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Diretório das saídas.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Modelo UVR (padrão: {DEFAULT_MODEL}).")
    parser.add_argument("--model-file-dir", type=Path, help="Diretório para armazenar modelos baixados.")
    parser.add_argument(
        "--engine",
        default="audio-separator",
        help="Executável do adaptador audio-separator (padrão: audio-separator).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Mostrar comandos sem executar separação.")
    parser.add_argument("--overwrite", action="store_true", help="Permitir sobrescrever saídas padronizadas.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source = args.input.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not source.exists():
        print(f"Erro: arquivo de entrada não encontrado: {source}", file=sys.stderr)
        return 2
    if source.suffix.lower() not in SUPPORTED_AUDIO_SUFFIXES:
        print(f"Aviso: extensão não reconhecida pelo adaptador: {source.suffix}")

    engine = executable(args.engine)
    ffmpeg = executable("ffmpeg")
    warnings: list[str] = []

    if engine is None:
        message = (
            "Executável audio-separator não encontrado. Instale com "
            "python3 -m pip install audio-separator e tente novamente."
        )
        if not args.dry_run:
            print(f"Erro: {message}", file=sys.stderr)
            return 3
        warnings.append(message)
        engine = args.engine

    if ffmpeg is None:
        message = "FFmpeg não encontrado no PATH; ele é necessário para normalizar a voz."
        if not args.dry_run:
            print(f"Erro: {message}", file=sys.stderr)
            return 3
        warnings.append(message)
        ffmpeg = "ffmpeg"

    before = set(output_dir.rglob("*"))
    command = [
        engine,
        str(source),
        "--model_filename",
        args.model,
        "--output_format",
        "WAV",
        "--output_dir",
        str(output_dir),
    ]
    if args.model_file_dir:
        command.extend(["--model_file_dir", str(args.model_file_dir.expanduser().resolve())])

    print(f"Entrada: {source}")
    print(f"Saída: {output_dir}")
    print(f"Modelo UVR: {args.model}")
    result = run(command, dry_run=args.dry_run)

    if args.dry_run:
        print("Simulação concluída. Nenhum arquivo foi processado.")
        return 0

    if result and result.stdout:
        print(result.stdout.strip())
    if result and result.stderr:
        print(result.stderr.strip(), file=sys.stderr)

    generated = find_outputs(output_dir, before)
    voice = choose_stem(generated, VOICE_TOKENS)
    accompaniment = choose_stem(generated, ACCOMPANIMENT_TOKENS)
    if voice is None:
        raise SeparationError(
            "A separação terminou, mas nenhuma saída vocal foi localizada. "
            "Verifique o log do audio-separator e os nomes dos stems gerados."
        )
    if accompaniment is None:
        warnings.append("Nenhum stem de acompanhamento foi identificado automaticamente.")

    raw_voice = copy_as(voice, output_dir / "voz_isolada_raw.wav", args.overwrite)
    eleven_voice = unique_target(output_dir / "voz_para_elevenlabs.wav", args.overwrite)
    normalize_voice(ffmpeg, raw_voice, eleven_voice, dry_run=False)

    accompaniment_target = None
    if accompaniment is not None:
        accompaniment_target = copy_as(
            accompaniment,
            output_dir / "acompanhamento_residual.wav",
            args.overwrite,
        )

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": str(source),
        "engine": str(engine),
        "model": args.model,
        "outputs": {
            "voice_raw": str(raw_voice),
            "voice_for_elevenlabs": str(eleven_voice),
            "accompaniment_residual": str(accompaniment_target) if accompaniment_target else None,
        },
        "warnings": warnings,
        "notes": [
            "A faixa residual não deve ser interpretada como pandeiro puro.",
            "Ouvir a voz isolada antes de iniciar a tradução.",
            "Manter o arquivo original para comparação e recuperação.",
        ],
    }
    manifest_path = output_dir / "separacao_manifest.json"
    write_manifest(manifest_path, manifest)

    print(f"Voz isolada: {raw_voice}")
    print(f"Voz para ElevenLabs: {eleven_voice}")
    if accompaniment_target:
        print(f"Acompanhamento residual: {accompaniment_target}")
    print(f"Manifesto: {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(f"Erro ao executar separação: código {error.returncode}", file=sys.stderr)
        if error.stdout:
            print(error.stdout, file=sys.stderr)
        if error.stderr:
            print(error.stderr, file=sys.stderr)
        raise SystemExit(error.returncode or 1)
    except SeparationError as error:
        print(f"Erro: {error}", file=sys.stderr)
        raise SystemExit(1)
