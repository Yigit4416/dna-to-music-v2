from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ncbi import fetch_sequence
from .sonifier import SonificationConfig, load_sequence_from_file, sonify_sequence, write_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DNA dizisini deterministik solo piyano MIDI'ye donusturur.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="FASTA veya ham DNA dosya yolu.")
    source.add_argument("--sequence", help="Ham DNA dizisi.")
    source.add_argument("--accession", help="NCBI accession numarasi.")

    parser.add_argument("--email", help="NCBI Entrez email adresi.")
    parser.add_argument("--api-key", help="NCBI API key.")
    parser.add_argument("--ncbi-db", default="nucleotide", help="NCBI veritabani. Varsayilan: nucleotide")
    parser.add_argument("--output", type=Path, required=True, help="Cikacak MIDI dosyasi.")
    parser.add_argument("--musicxml-output", type=Path, help="Istege bagli MusicXML cikisi.")
    parser.add_argument("--metadata-output", type=Path, help="Istege bagli JSON ozet cikisi.")
    parser.add_argument("--duration-seconds", type=int, default=120, help="Parca suresi. Varsayilan: 120")
    parser.add_argument("--window", type=int, default=300, help="Pencere boyu. Varsayilan: 300")
    parser.add_argument("--stride", type=int, default=150, help="Kayma miktari. Varsayilan: 150")
    parser.add_argument("--title", default="DNA Sonification", help="Parca basligi.")
    parser.add_argument("--enable-add9", action="store_true", help="Her 4 olcude en fazla bir add9 suslemeyi aktif eder.")
    return parser


def resolve_sequence(args: argparse.Namespace) -> tuple[str, str]:
    if args.input:
        return load_sequence_from_file(args.input)
    if args.sequence:
        return args.sequence, "raw-sequence"
    if args.accession:
        record = fetch_sequence(
            accession=args.accession,
            email=args.email,
            db=args.ncbi_db,
            api_key=args.api_key,
        )
        return record.sequence, record.description
    raise ValueError("Bir DNA kaynagi secilmelidir.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.duration_seconds <= 0:
        parser.error("--duration-seconds pozitif olmali.")
    if args.window <= 0 or args.stride <= 0:
        parser.error("--window ve --stride pozitif olmali.")
    if args.accession and not args.email:
        parser.error("NCBI kullaniminda --email zorunludur.")

    try:
        sequence, label = resolve_sequence(args)
        config = SonificationConfig(
            duration_seconds=args.duration_seconds,
            window_size=args.window,
            stride=args.stride,
            enable_add9=args.enable_add9,
            title=args.title,
        )
        score, summary = sonify_sequence(sequence=sequence, config=config, source_label=label)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        score.write("midi", fp=str(args.output))

        if args.musicxml_output:
            args.musicxml_output.parent.mkdir(parents=True, exist_ok=True)
            score.write("musicxml", fp=str(args.musicxml_output))

        if args.metadata_output:
            args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
            write_summary(args.metadata_output, summary)

    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"Hata: {exc}", file=sys.stderr)
        return 1

    print(
        f"Olustu: {args.output} | {summary.tonic} {summary.mode} | "
        f"{summary.progression} | {summary.bpm} BPM | {summary.measures} olcu"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

