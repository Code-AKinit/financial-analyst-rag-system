"""
Document chunking strategies.

Implements semantic chunking with structure preservation.
"""

import re
from typing import List

from src.config.logging_config import get_logger

logger = get_logger(__name__)


def semantic_chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> List[str]:
    """
    Create semantic chunks from text, preserving structure.

    Tries to break at natural boundaries (paragraphs, sentences) rather than
    arbitrary character counts.

    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks for context continuity

    Returns:
        List[str]: Text chunks
    """
    if not text or not text.strip():
        return []

    # Split into paragraphs first
    paragraphs = text.split("\n\n")
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph)

        # If single paragraph is too large, split it
        if paragraph_length > chunk_size:
            # First, save current chunk if any
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_length = 0

            # Split large paragraph into sentences
            sentence_chunks = _chunk_large_paragraph(paragraph, chunk_size, overlap)
            chunks.extend(sentence_chunks)
            continue

        # Check if adding this paragraph exceeds chunk size
        if current_length + paragraph_length > chunk_size and current_chunk:
            # Save current chunk
            chunks.append("\n\n".join(current_chunk))

            # Start new chunk with overlap
            overlap_text = _get_overlap_text(current_chunk, overlap)
            current_chunk = [overlap_text, paragraph] if overlap_text else [paragraph]
            current_length = sum(len(p) for p in current_chunk)
        else:
            # Add to current chunk
            current_chunk.append(paragraph)
            current_length += paragraph_length + 2  # +2 for \n\n

    # Add final chunk
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    logger.debug("text_chunked", total_chunks=len(chunks), avg_size=sum(len(c) for c in chunks) // len(chunks) if chunks else 0)

    return chunks


def _chunk_large_paragraph(paragraph: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Chunk a large paragraph by sentences.

    Args:
        paragraph: Large paragraph to split
        chunk_size: Target chunk size
        overlap: Overlap size

    Returns:
        List[str]: Paragraph chunks
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', paragraph)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)

        # If single sentence is too large, force split
        if sentence_length > chunk_size:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0

            # Force split by words
            word_chunks = _force_split_by_words(sentence, chunk_size)
            chunks.extend(word_chunks)
            continue

        # Check if adding this sentence exceeds chunk size
        if current_length + sentence_length > chunk_size and current_chunk:
            # Save current chunk
            chunks.append(" ".join(current_chunk))

            # Start new chunk with overlap
            overlap_sentences = _get_overlap_sentences(current_chunk, overlap)
            current_chunk = overlap_sentences + [sentence]
            current_length = sum(len(s) for s in current_chunk)
        else:
            # Add to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space

    # Add final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def _force_split_by_words(text: str, chunk_size: int) -> List[str]:
    """
    Force split text by words when no natural boundary exists.

    Args:
        text: Text to split
        chunk_size: Target chunk size

    Returns:
        List[str]: Text chunks
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word)

        if current_length + word_length > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length + 1  # +1 for space

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def _get_overlap_text(chunks: List[str], overlap_size: int) -> str:
    """
    Get overlap text from end of chunks.

    Args:
        chunks: Current chunks
        overlap_size: Target overlap size

    Returns:
        str: Overlap text
    """
    if not chunks:
        return ""

    # Get last chunk
    last_chunk = chunks[-1]

    # If last chunk is smaller than overlap, use entire chunk
    if len(last_chunk) <= overlap_size:
        return last_chunk

    # Otherwise, get last overlap_size characters at word boundary
    text = last_chunk[-overlap_size:]

    # Find first space to avoid cutting words
    first_space = text.find(" ")
    if first_space != -1:
        text = text[first_space + 1 :]

    return text


def _get_overlap_sentences(sentences: List[str], overlap_size: int) -> List[str]:
    """
    Get overlap sentences from end of sentence list.

    Args:
        sentences: Current sentences
        overlap_size: Target overlap size

    Returns:
        List[str]: Overlap sentences
    """
    if not sentences:
        return []

    overlap_sentences = []
    current_length = 0

    # Add sentences from end until we reach overlap size
    for sentence in reversed(sentences):
        sentence_length = len(sentence)

        if current_length + sentence_length > overlap_size:
            break

        overlap_sentences.insert(0, sentence)
        current_length += sentence_length

    return overlap_sentences


def fixed_size_chunking(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> List[str]:
    """
    Simple fixed-size chunking with overlap.

    Falls back to this if semantic chunking fails.

    Args:
        text: Text to chunk
        chunk_size: Chunk size in characters
        overlap: Overlap size

    Returns:
        List[str]: Text chunks
    """
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks
