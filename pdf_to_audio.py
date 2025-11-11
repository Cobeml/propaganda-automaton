#!/usr/bin/env python3
"""
PDF to Audiobook Converter
Converts PDF text to speech using Kokoro TTS with intelligent chunking.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from pdf_extractor import extract_pdf_text, clean_text_rules, chunk_by_paragraphs, preview_extraction


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be used as a filename.
    Removes or replaces invalid characters.
    """
    # Remove or replace invalid characters
    name = name.replace('/', '_').replace('\\', '_')
    name = name.replace(':', '-').replace('*', '_')
    name = name.replace('?', '').replace('"', '').replace('<', '').replace('>', '')
    name = name.replace('|', '_')

    # Limit length
    if len(name) > 200:
        name = name[:200]

    return name.strip()


def create_output_directory(pdf_path: str, output_base: str) -> Path:
    """
    Create output directory based on PDF filename.

    Args:
        pdf_path: Path to the PDF file
        output_base: Base output directory

    Returns:
        Path to the created output directory
    """
    pdf_name = Path(pdf_path).stem
    sanitized_name = sanitize_filename(pdf_name)

    # Truncate extremely long names
    if len(sanitized_name) > 100:
        sanitized_name = sanitized_name[:100]

    output_dir = Path(output_base) / sanitized_name
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def process_pdf_to_audio(
    pdf_path: str,
    output_dir: str = "voices/audiobooks",
    voice: str = "bm_lewis",
    lang_code: str = "a",
    speed: float = 1.0,
    page_start: Optional[int] = None,
    page_end: Optional[int] = None,
    dry_run: bool = False,
    max_chunk_size: int = 3000,
    min_chunk_size: int = 500
) -> Dict:
    """
    Main processing pipeline: PDF -> Text -> Clean -> Chunk -> Audio

    Args:
        pdf_path: Path to the PDF file
        output_dir: Base directory for output files
        voice: Voice to use for TTS
        lang_code: Language code for TTS
        speed: Speech speed multiplier
        page_start: Starting page (1-indexed)
        page_end: Ending page (1-indexed)
        dry_run: If True, only preview extraction without generating audio
        max_chunk_size: Maximum characters per chunk
        min_chunk_size: Minimum characters per chunk

    Returns:
        Dictionary with processing results and metadata
    """
    print("=" * 70)
    print("PDF to Audiobook Converter")
    print("=" * 70)
    print(f"PDF: {pdf_path}")
    print(f"Voice: {voice}")
    print(f"Speed: {speed}x")

    if page_start or page_end:
        page_range_str = f"Pages {page_start or '1'} to {page_end or 'end'}"
        print(f"Page Range: {page_range_str}")

    print()

    # Step 1: Extract text from PDF
    print("[1/4] Extracting text from PDF...")
    start_time = time.time()

    try:
        raw_text, metadata = extract_pdf_text(pdf_path, page_start, page_end)
    except Exception as e:
        print(f"ERROR: Failed to extract text from PDF: {e}")
        return {"success": False, "error": str(e)}

    extract_time = time.time() - start_time

    print(f"  ✓ Extracted {len(raw_text):,} characters from {metadata['pages_extracted']} pages")
    print(f"    (Total pages in PDF: {metadata['total_pages']})")
    print(f"    Time: {extract_time:.1f}s")
    print()

    # Step 2: Clean text
    print("[2/4] Cleaning text...")
    start_time = time.time()

    cleaned_text = clean_text_rules(raw_text)
    clean_time = time.time() - start_time

    removed_chars = len(raw_text) - len(cleaned_text)
    print(f"  ✓ Cleaned text: {len(cleaned_text):,} characters")
    print(f"    Removed {removed_chars:,} characters ({removed_chars/len(raw_text)*100:.1f}%)")
    print(f"    Time: {clean_time:.1f}s")
    print()

    # Step 3: Chunk text
    print("[3/4] Chunking text into segments...")
    start_time = time.time()

    chunks = chunk_by_paragraphs(cleaned_text, max_chunk_size, min_chunk_size)
    chunk_time = time.time() - start_time

    chunk_lengths = [len(text) for _, text in chunks]
    avg_length = sum(chunk_lengths) / len(chunks) if chunks else 0

    print(f"  ✓ Created {len(chunks)} chunks")
    print(f"    Average chunk size: {int(avg_length):,} characters")
    print(f"    Min: {min(chunk_lengths):,}, Max: {max(chunk_lengths):,}")
    print(f"    Time: {chunk_time:.1f}s")
    print()

    # Estimate audio duration
    word_count = len(cleaned_text.split())
    estimated_minutes = word_count / 150  # ~150 words per minute
    estimated_hours = estimated_minutes / 60

    print(f"Estimated audio duration: {estimated_hours:.1f} hours ({estimated_minutes:.0f} minutes)")
    print(f"Word count: {word_count:,}")
    print()

    # If dry run, stop here and show preview
    if dry_run:
        print("=" * 70)
        print("DRY RUN - Preview Only (no audio generated)")
        print("=" * 70)
        print()
        print("First chunk preview:")
        print("-" * 70)
        print(chunks[0][1][:500] + "..." if len(chunks[0][1]) > 500 else chunks[0][1])
        print("-" * 70)
        print()

        return {
            "success": True,
            "dry_run": True,
            "metadata": metadata,
            "total_chunks": len(chunks),
            "word_count": word_count,
            "estimated_duration_hours": round(estimated_hours, 1)
        }

    # Step 4: Generate audio
    # Import audio_gen only when needed (not required for dry-run)
    from audio_gen import generate_audio

    print("[4/4] Generating audio files...")
    print(f"This will take approximately {estimated_hours * 60:.0f} minutes")
    print()

    # Create output directory
    output_path = create_output_directory(pdf_path, output_dir)
    print(f"Output directory: {output_path}")
    print()

    generated_files = []
    chunk_metadata = []
    total_start_time = time.time()

    for chunk_num, chunk_text in chunks:
        chunk_start_time = time.time()

        # Create filename: chunk_001.wav, chunk_002.wav, etc.
        chunk_filename = f"chunk_{chunk_num:03d}.wav"
        chunk_output_path = output_path / chunk_filename

        print(f"Processing chunk {chunk_num}/{len(chunks)}...")
        print(f"  Characters: {len(chunk_text):,}")

        try:
            # Generate audio using existing audio_gen module
            # Note: generate_audio returns a list, but we're giving it a single output path
            audio_files = generate_audio(
                text=chunk_text,
                output_path=str(chunk_output_path),
                voice=voice,
                lang_code=lang_code,
                speed=speed,
                split_pattern=None  # Don't split further - our chunks are already optimized
            )

            chunk_time = time.time() - chunk_start_time

            # Store metadata
            chunk_info = {
                "chunk_num": chunk_num,
                "filename": chunk_filename,
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "generation_time_seconds": round(chunk_time, 2),
                "text_preview": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
            }

            chunk_metadata.append(chunk_info)
            generated_files.extend(audio_files)

            # Progress update
            elapsed = time.time() - total_start_time
            avg_time_per_chunk = elapsed / chunk_num
            remaining_chunks = len(chunks) - chunk_num
            estimated_remaining = avg_time_per_chunk * remaining_chunks

            print(f"  ✓ Generated: {chunk_filename}")
            print(f"    Time: {chunk_time:.1f}s")
            print(f"    Progress: {chunk_num}/{len(chunks)} ({chunk_num/len(chunks)*100:.1f}%)")
            print(f"    Estimated time remaining: {estimated_remaining/60:.1f} minutes")
            print()

        except Exception as e:
            print(f"  ERROR generating audio for chunk {chunk_num}: {e}")
            print("  Continuing with next chunk...")
            print()

    total_time = time.time() - total_start_time

    # Save manifest JSON
    manifest = {
        "pdf_info": {
            "filename": metadata["file_name"],
            "total_pages": metadata["total_pages"],
            "pages_extracted": metadata["pages_extracted"],
            "page_range": metadata["page_range"]
        },
        "generation_info": {
            "voice": voice,
            "lang_code": lang_code,
            "speed": speed,
            "generated_at": datetime.now().isoformat(),
            "total_generation_time_seconds": round(total_time, 2),
            "total_generation_time_minutes": round(total_time / 60, 1)
        },
        "text_stats": {
            "total_characters": len(cleaned_text),
            "total_words": word_count,
            "total_chunks": len(chunks),
            "avg_chunk_length": int(avg_length)
        },
        "chunks": chunk_metadata
    }

    manifest_path = output_path / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print("GENERATION COMPLETE!")
    print("=" * 70)
    print(f"Generated {len(generated_files)} audio file(s)")
    print(f"Output directory: {output_path}")
    print(f"Total time: {total_time/60:.1f} minutes ({total_time/3600:.2f} hours)")
    print(f"Manifest saved: {manifest_path}")
    print()

    return {
        "success": True,
        "output_directory": str(output_path),
        "generated_files": generated_files,
        "manifest": manifest,
        "total_time_seconds": round(total_time, 2)
    }


def main():
    """
    CLI interface for PDF to audiobook conversion.
    """
    parser = argparse.ArgumentParser(
        description="Convert PDF to audiobook using Kokoro TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process entire book
  python pdf_to_audio.py --pdf-path "book.pdf"

  # Process first 50 pages only
  python pdf_to_audio.py --pdf-path "book.pdf" --page-start 1 --page-end 50

  # Use different voice and speed
  python pdf_to_audio.py --pdf-path "book.pdf" --voice am_adam --speed 1.2

  # Preview without generating audio (dry run)
  python pdf_to_audio.py --pdf-path "book.pdf" --dry-run

Available voices:
  Male: bm_lewis, am_adam, am_michael
  Female: af_heart, af_bella, af_sarah, af_nicole, bf_emma, bf_isabella
        """
    )

    parser.add_argument(
        "--pdf-path",
        required=True,
        help="Path to the PDF file"
    )

    parser.add_argument(
        "--output-dir",
        default="voices/audiobooks",
        help="Base directory for output files (default: voices/audiobooks)"
    )

    parser.add_argument(
        "--voice",
        default="bm_lewis",
        help="Voice to use for TTS (default: bm_lewis)"
    )

    parser.add_argument(
        "--lang-code",
        default="a",
        help="Language code: a=American English, b=British English (default: a)"
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speech speed multiplier (default: 1.0)"
    )

    parser.add_argument(
        "--page-start",
        type=int,
        help="Starting page number (1-indexed, inclusive)"
    )

    parser.add_argument(
        "--page-end",
        type=int,
        help="Ending page number (1-indexed, inclusive)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview extraction and chunking without generating audio"
    )

    parser.add_argument(
        "--max-chunk-size",
        type=int,
        default=3000,
        help="Maximum characters per chunk (default: 3000)"
    )

    parser.add_argument(
        "--min-chunk-size",
        type=int,
        default=500,
        help="Minimum characters per chunk (default: 500)"
    )

    args = parser.parse_args()

    # Validate PDF path
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        sys.exit(1)

    # Run conversion
    result = process_pdf_to_audio(
        pdf_path=args.pdf_path,
        output_dir=args.output_dir,
        voice=args.voice,
        lang_code=args.lang_code,
        speed=args.speed,
        page_start=args.page_start,
        page_end=args.page_end,
        dry_run=args.dry_run,
        max_chunk_size=args.max_chunk_size,
        min_chunk_size=args.min_chunk_size
    )

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
