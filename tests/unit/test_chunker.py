"""
Unit tests for src/models/chunker.py.
Pure function — no mocks, no DB.
"""

import pytest

from src.models.chunker import chunk_text


class TestChunkText:

    def test_empty_text_returns_empty(self):
        """chunk_text('') returns []."""
        assert chunk_text("") == []

    def test_whitespace_only_returns_empty(self):
        """Whitespace-only input returns []."""
        assert chunk_text("   \n\t  ") == []

    def test_short_text_returns_one_chunk(self):
        """Text shorter than chunk_size returns a single chunk equal to the input."""
        text = "Apple files for bankruptcy protection."
        result = chunk_text(text, chunk_size=300, overlap=50)
        assert result == [text]
        assert len(result) == 1

    def test_exact_chunk_size_returns_one_chunk(self):
        """Text with exactly chunk_size words returns 1 chunk."""
        words = ["word"] * 300
        text = " ".join(words)
        result = chunk_text(text, chunk_size=300, overlap=50)
        assert len(result) == 1
        assert result[0] == text

    def test_large_text_produces_multiple_chunks(self):
        """1000-word text with chunk_size=300, overlap=50 → multiple chunks."""
        words = [f"w{i}" for i in range(1000)]
        text = " ".join(words)
        result = chunk_text(text, chunk_size=300, overlap=50)
        assert len(result) > 1

    def test_overlap_shares_content_between_adjacent_chunks(self):
        """Adjacent chunks share overlap words at the boundary."""
        words = [f"w{i}" for i in range(400)]
        text = " ".join(words)
        result = chunk_text(text, chunk_size=300, overlap=50)
        # Last 50 words of chunk 0 should be the first 50 words of chunk 1
        chunk0_words = result[0].split()
        chunk1_words = result[1].split()
        assert chunk0_words[-50:] == chunk1_words[:50]

    def test_last_chunk_does_not_exceed_chunk_size(self):
        """Every chunk has at most chunk_size words."""
        words = [f"w{i}" for i in range(750)]
        text = " ".join(words)
        result = chunk_text(text, chunk_size=300, overlap=50)
        for chunk in result:
            assert len(chunk.split()) <= 300

    def test_custom_chunk_size_and_overlap(self):
        """Custom parameters are respected."""
        words = [f"w{i}" for i in range(20)]
        text = " ".join(words)
        result = chunk_text(text, chunk_size=10, overlap=3)
        # words 0-9 → chunk 0, words 7-16 → chunk 1, words 14-19 → chunk 2
        assert len(result) == 3
        assert result[0] == " ".join(words[:10])
        assert result[1] == " ".join(words[7:17])
        assert result[2] == " ".join(words[14:])
