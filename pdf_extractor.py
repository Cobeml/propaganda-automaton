"""
PDF Text Extraction and Cleaning Utilities
Optimized for academic texts and audiobook generation.
"""

import re
from pathlib import Path
from typing import Optional, List, Tuple
from pypdf import PdfReader


def extract_pdf_text(
    pdf_path: str,
    page_start: Optional[int] = None,
    page_end: Optional[int] = None
) -> Tuple[str, dict]:
    """
    Extract text from a PDF file with optional page range.

    Args:
        pdf_path: Path to the PDF file
        page_start: Starting page number (1-indexed, inclusive). None = from beginning
        page_end: Ending page number (1-indexed, inclusive). None = to end

    Returns:
        Tuple of (extracted_text, metadata_dict)
        metadata includes: total_pages, pages_extracted, page_range
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    # Handle page range (convert to 0-indexed)
    start_idx = (page_start - 1) if page_start is not None else 0
    end_idx = page_end if page_end is not None else total_pages

    # Validate range
    start_idx = max(0, start_idx)
    end_idx = min(total_pages, end_idx)

    if start_idx >= end_idx:
        raise ValueError(f"Invalid page range: start={page_start}, end={page_end}")

    # Extract text from specified pages
    extracted_text = []
    for page_num in range(start_idx, end_idx):
        page = reader.pages[page_num]
        text = page.extract_text()
        extracted_text.append(text)

    full_text = "\n".join(extracted_text)

    metadata = {
        "total_pages": total_pages,
        "pages_extracted": end_idx - start_idx,
        "page_range": f"{start_idx + 1}-{end_idx}",
        "file_name": pdf_path.name
    }

    return full_text, metadata


def clean_text_rules(raw_text: str) -> str:
    """
    Apply rule-based cleaning to remove common PDF artifacts.
    Optimized for academic/philosophical texts.

    Args:
        raw_text: Raw extracted text from PDF

    Returns:
        Cleaned text ready for TTS processing
    """
    text = raw_text

    # 1. Fix hyphenation at line breaks (e.g., "knowl-\nedge" -> "knowledge")
    # This is the most common PDF artifact
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # 2. Remove page numbers (common patterns)
    # Match standalone numbers at start/end of lines
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\[\s*\d+\s*\]\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)

    # 3. Remove common header/footer patterns
    # (You might need to adjust these based on the specific book)
    text = re.sub(r'^\s*Chapter\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)

    # 4. Strip footnote markers (but keep the text)
    # Convert [1], [2] etc to just spaces to maintain flow
    text = re.sub(r'\[\d+\]', ' ', text)
    text = re.sub(r'\(\d+\)', ' ', text)

    # 5. Normalize multiple spaces
    text = re.sub(r' {2,}', ' ', text)

    # 6. Normalize line breaks - remove single line breaks but keep paragraph breaks
    # Replace single newlines with spaces, but preserve double+ newlines (paragraph breaks)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

    # 7. Normalize multiple newlines to double newlines (paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 8. Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # 9. Remove empty lines at the start and end
    text = text.strip()

    # 10. Fix common OCR/PDF artifacts in academic texts
    # Replace smart quotes with regular quotes (optional, but helps with some TTS)
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # " "
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # ' '
    text = text.replace('\u2013', '-').replace('\u2014', '-')  # – —

    return text


def chunk_by_paragraphs(
    text: str,
    max_chunk_size: int = 3000,
    min_chunk_size: int = 500
) -> List[Tuple[int, str]]:
    """
    Split text into smart chunks based on paragraph breaks.
    Ensures chunks are not too large or too small for optimal TTS generation.

    Args:
        text: Cleaned text to chunk
        max_chunk_size: Maximum characters per chunk (default: 3000)
        min_chunk_size: Minimum characters per chunk (default: 500)

    Returns:
        List of (chunk_number, chunk_text) tuples
    """
    # Split by paragraph breaks (double newlines)
    paragraphs = text.split('\n\n')

    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_length = len(para)

        # If single paragraph is larger than max_chunk_size, split it by sentences
        if para_length > max_chunk_size:
            # Try to split by sentences (., !, ?)
            sentences = re.split(r'([.!?]+\s+)', para)

            # Recombine sentence with its punctuation
            sentence_parts = []
            for i in range(0, len(sentences) - 1, 2):
                if i + 1 < len(sentences):
                    sentence_parts.append(sentences[i] + sentences[i + 1])
                else:
                    sentence_parts.append(sentences[i])

            # Add remaining part if odd number of splits
            if len(sentences) % 2 == 1:
                sentence_parts.append(sentences[-1])

            # Process sentences like paragraphs
            for sentence in sentence_parts:
                sentence = sentence.strip()
                if not sentence:
                    continue

                sentence_length = len(sentence)

                if current_length + sentence_length > max_chunk_size and current_chunk:
                    # Flush current chunk
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = [sentence]
                    current_length = sentence_length
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_length
        else:
            # Normal paragraph processing
            if current_length + para_length > max_chunk_size and current_chunk:
                # Flush current chunk if adding this paragraph would exceed max
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length

    # Flush remaining chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    # Post-process: merge chunks that are too small
    merged_chunks = []
    i = 0
    while i < len(chunks):
        chunk = chunks[i]

        # If chunk is too small and there's a next chunk, try to merge
        if len(chunk) < min_chunk_size and i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            if len(chunk) + len(next_chunk) <= max_chunk_size:
                # Merge with next chunk
                merged_chunk = chunk + '\n\n' + next_chunk
                merged_chunks.append(merged_chunk)
                i += 2  # Skip next chunk since we merged it
                continue

        merged_chunks.append(chunk)
        i += 1

    # Return numbered chunks
    numbered_chunks = [(idx + 1, chunk) for idx, chunk in enumerate(merged_chunks)]

    return numbered_chunks


def preview_extraction(
    pdf_path: str,
    page_start: Optional[int] = None,
    page_end: Optional[int] = None,
    preview_chars: int = 1000
) -> dict:
    """
    Preview PDF extraction without generating audio.
    Useful for validating the extraction and cleaning process.

    Args:
        pdf_path: Path to the PDF file
        page_start: Starting page number (optional)
        page_end: Ending page number (optional)
        preview_chars: Number of characters to show in preview (default: 1000)

    Returns:
        Dictionary with preview information
    """
    # Extract text
    raw_text, metadata = extract_pdf_text(pdf_path, page_start, page_end)

    # Clean text
    cleaned_text = clean_text_rules(raw_text)

    # Chunk text
    chunks = chunk_by_paragraphs(cleaned_text)

    # Calculate statistics
    chunk_lengths = [len(chunk_text) for _, chunk_text in chunks]
    avg_chunk_length = sum(chunk_lengths) / len(chunk_lengths) if chunks else 0

    # Estimate audio duration (average speaking rate: ~150 words per minute)
    word_count = len(cleaned_text.split())
    estimated_minutes = word_count / 150

    preview = {
        "metadata": metadata,
        "raw_text_length": len(raw_text),
        "cleaned_text_length": len(cleaned_text),
        "total_chunks": len(chunks),
        "avg_chunk_length": int(avg_chunk_length),
        "min_chunk_length": min(chunk_lengths) if chunks else 0,
        "max_chunk_length": max(chunk_lengths) if chunks else 0,
        "word_count": word_count,
        "estimated_audio_duration_minutes": round(estimated_minutes, 1),
        "estimated_audio_duration_hours": round(estimated_minutes / 60, 1),
        "first_chunk_preview": chunks[0][1][:preview_chars] if chunks else "",
        "first_3_chunks_info": [
            {"chunk_num": num, "length": len(text), "preview": text[:100] + "..."}
            for num, text in chunks[:3]
        ]
    }

    return preview


if __name__ == "__main__":
    # Example usage
    print("PDF Extractor Utilities")
    print("Import this module to use: extract_pdf_text, clean_text_rules, chunk_by_paragraphs")
