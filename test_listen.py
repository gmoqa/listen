#!/usr/bin/env python3
"""
Tests for listen.py main functionality
"""

import pytest
import tempfile
import os
import sys
import subprocess


class TestCLIHelp:
    """Test CLI help and usage information"""

    def test_help_flag(self):
        """Test that --help flag works"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 0
        assert 'usage:' in result.stdout.lower()
        assert '--file' in result.stdout
        assert '--language' in result.stdout
        assert '--model' in result.stdout

    def test_help_shows_file_mode(self):
        """Test that help shows file processing mode"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '-h'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 0
        assert '-f' in result.stdout or '--file' in result.stdout
        assert 'Transcribe audio from file' in result.stdout


class TestFileMode:
    """Test file processing mode"""

    def test_file_not_found(self):
        """Test error handling when file doesn't exist"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '-f', '/nonexistent/file.mp3'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 1
        assert 'File not found' in result.stderr or 'not found' in result.stderr.lower()

    def test_file_is_directory(self):
        """Test error handling when path is a directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, 'listen.py', '-f', tmpdir],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            assert result.returncode == 1
            assert 'Not a file' in result.stderr or 'not a file' in result.stderr.lower()

    def test_file_argument_parsing(self):
        """Test that -f and --file arguments are recognized"""
        # Test with empty file to avoid transcription
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # This will fail during transcription but should parse the argument
            result = subprocess.run(
                [sys.executable, 'listen.py', '-f', tmp_path, '-v'],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            # Check that it attempted to process the file (may fail on transcription)
            # The important part is that it didn't fail on argument parsing
            assert 'File not found' not in result.stderr
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestConfigCommand:
    """Test config subcommand"""

    def test_config_help(self):
        """Test that config --help works"""
        result = subprocess.run(
            [sys.executable, 'listen.py', 'config', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 0
        assert 'Usage:' in result.stdout or 'usage:' in result.stdout
        assert '--show' in result.stdout
        assert '--reset' in result.stdout

    def test_config_show(self):
        """Test that config --show displays configuration"""
        result = subprocess.run(
            [sys.executable, 'listen.py', 'config', '--show'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 0
        assert 'language:' in result.stdout.lower()
        assert 'model:' in result.stdout.lower()


class TestArgumentParsing:
    """Test CLI argument parsing"""

    def test_language_argument(self):
        """Test that language argument is accepted"""
        # We're just testing parsing, not full execution
        # Using a nonexistent file will fail fast after parsing
        result = subprocess.run(
            [sys.executable, 'listen.py', '-f', '/tmp/fake.wav', '-l', 'es'],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # It should fail on file not found, not on argument parsing
        assert 'File not found' in result.stderr or 'not found' in result.stderr.lower()

    def test_model_argument(self):
        """Test that model argument is accepted"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '-f', '/tmp/fake.wav', '-m', 'tiny'],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # It should fail on file not found, not on argument parsing
        assert 'File not found' in result.stderr or 'not found' in result.stderr.lower()

    def test_verbose_argument(self):
        """Test that verbose argument is accepted"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '-f', '/tmp/fake.wav', '-v'],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # It should fail on file not found, not on argument parsing
        assert 'File not found' in result.stderr or 'not found' in result.stderr.lower()


class TestValidation:
    """Test input validation"""

    def test_empty_file_path(self):
        """Test handling of empty file path"""
        # Create an empty file to test size validation
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Empty audio file should exist but may fail during processing
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) == 0

            # The validation should catch this during transcription
            result = subprocess.run(
                [sys.executable, 'listen.py', '-f', tmp_path],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            # Should handle empty file gracefully (may error during transcription)
            assert result.returncode != 0 or 'Processing file:' in result.stderr
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestServerMode:
    """Test server mode basics"""

    def test_server_mode_flag(self):
        """Test that server mode flag is recognized"""
        # Start server and immediately kill it
        process = subprocess.Popen(
            [sys.executable, 'listen.py', '-s'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        try:
            # Wait a bit to see if it starts
            import time
            time.sleep(1)

            # Check if process is running
            assert process.poll() is None  # None means still running

            # Try to read some output
            # Note: This is a basic test, full server testing would need more setup
        finally:
            process.terminate()
            process.wait(timeout=5)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
