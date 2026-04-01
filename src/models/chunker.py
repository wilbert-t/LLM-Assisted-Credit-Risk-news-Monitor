"""
Text chunking utility for embedding pipeline.

Usage:
    from src.models.chunker import chunk_text

    chunks = chunk_text(text, chunk_size=300, overlap=50)
    # ["first 300 words...", "overlapping 300 words...", ...]
"""

from __future__ import annotations

from typing import List


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping word-level chunks.

    Args:
        text:       Input text string.
        chunk_size: Maximum words per chunk (default 300).
        overlap:    Number of words shared between adjacent chunks (default 50).

    Returns:
        List of chunk strings. Returns [] for blank input.
        Returns a single-element list if text fits within chunk_size words.
    """
    words = text.split()
    if not words:
        return []
    if len(words) <= chunk_size:
        return [" ".join(words)]

    chunks: List[str] = []
    start = 0
    step = chunk_size - overlap

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += step

    return chunks
