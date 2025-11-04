#!/usr/bin/env python3
"""
Shared pytest fixtures and configuration
"""

import pytest
import tempfile
import os


@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        # Write a minimal WAV header (empty file)
        # RIFF header
        tmp.write(b'RIFF')
        tmp.write((36).to_bytes(4, 'little'))  # File size - 8
        tmp.write(b'WAVE')

        # fmt chunk
        tmp.write(b'fmt ')
        tmp.write((16).to_bytes(4, 'little'))  # Chunk size
        tmp.write((1).to_bytes(2, 'little'))   # Audio format (PCM)
        tmp.write((1).to_bytes(2, 'little'))   # Num channels
        tmp.write((16000).to_bytes(4, 'little'))  # Sample rate
        tmp.write((32000).to_bytes(4, 'little'))  # Byte rate
        tmp.write((2).to_bytes(2, 'little'))   # Block align
        tmp.write((16).to_bytes(2, 'little'))  # Bits per sample

        # data chunk
        tmp.write(b'data')
        tmp.write((0).to_bytes(4, 'little'))   # Data size

        tmp_path = tmp.name

    yield tmp_path

    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_config_dir(monkeypatch, temp_directory):
    """Mock the config directory to use a temp directory"""
    import config

    config_file = os.path.join(temp_directory, 'config.json')
    monkeypatch.setattr(config, 'get_config_path', lambda: config_file)

    yield temp_directory, config_file
