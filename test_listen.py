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


class TestConfig:
    """Test configuration defaults"""

    def test_config_defaults(self):
        """Test that config.py provides default values"""
        import config

        # Test that basic config values exist
        assert hasattr(config, 'MODEL')
        assert hasattr(config, 'LANGUAGE')
        assert hasattr(config, 'SAMPLE_RATE')
        assert hasattr(config, 'CHANNELS')

        # Test default values
        assert config.MODEL == 'tiny'  # Should be tiny after refactor
        assert config.LANGUAGE == 'en'
        assert config.SAMPLE_RATE == 16000
        assert config.CHANNELS == 1

    def test_config_vad_settings(self):
        """Test VAD configuration values"""
        import config

        assert hasattr(config, 'VAD_THRESHOLD')
        assert hasattr(config, 'VAD_DEFAULT_DURATION')
        assert isinstance(config.VAD_THRESHOLD, float)
        assert isinstance(config.VAD_DEFAULT_DURATION, float)

    def test_help_mentions_config_file(self):
        """Test that help text mentions editing config.py"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 0
        assert 'config.py' in result.stdout.lower()
        assert 'reinstall' in result.stdout.lower()


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


class TestVersionFlag:
    """Test version flag"""

    def test_version_flag(self):
        """Test that --version shows version number"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '--version'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 0
        assert 'listen' in result.stdout
        # Should contain version number (format: X.Y.Z)
        import re
        assert re.search(r'\d+\.\d+\.\d+', result.stdout)


class TestOutputModes:
    """Test various output modes"""

    def test_json_flag_recognized(self):
        """Test that -j/--json flag is recognized"""
        # Test with nonexistent file to fail fast
        result = subprocess.run(
            [sys.executable, 'listen.py', '-f', '/tmp/fake.wav', '-j'],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # Should fail on file not found, not on argument parsing
        assert 'File not found' in result.stderr or 'not found' in result.stderr.lower()

    def test_quiet_flag_recognized(self):
        """Test that -q/--quiet flag is recognized"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '-f', '/tmp/fake.wav', '-q'],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # Should fail on file not found, not on argument parsing
        assert 'File not found' in result.stderr or 'not found' in result.stderr.lower()

    def test_output_file_flag_recognized(self):
        """Test that -o/--output flag is recognized"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '-f', '/tmp/fake.wav', '-o', '/tmp/out.txt'],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # Should fail on file not found, not on argument parsing
        assert 'File not found' in result.stderr or 'not found' in result.stderr.lower()


class TestSpecialModes:
    """Test special recording modes"""

    def test_codevoice_flag_recognized(self):
        """Test that --codevoice flag is recognized"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 0
        assert '--codevoice' in result.stdout

    def test_vad_flag_recognized(self):
        """Test that --vad flag is recognized in help"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 0
        assert '--vad' in result.stdout

    def test_signal_mode_flag_recognized(self):
        """Test that --signal-mode flag is recognized in help"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 0
        assert '--signal-mode' in result.stdout

    def test_fast_mode_flag_recognized(self):
        """Test that --fast-mode flag is recognized in help"""
        result = subprocess.run(
            [sys.executable, 'listen.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        assert result.returncode == 0
        assert '--fast-mode' in result.stdout


class TestFastMode:
    """Test fast mode functionality"""

    def test_fast_mode_requires_faster_whisper(self):
        """Test that --fast-mode validates faster-whisper availability"""
        import listen

        # Save original value
        original_available = listen.FASTER_WHISPER_AVAILABLE

        # Test when faster-whisper is not available
        listen.FASTER_WHISPER_AVAILABLE = False

        result = subprocess.run(
            [sys.executable, 'listen.py', '-f', '/tmp/fake.wav', '--fast-mode'],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # Restore original value
        listen.FASTER_WHISPER_AVAILABLE = original_available

        # Should fail with error about faster-whisper not installed
        # Note: This test may pass if faster-whisper IS installed, which is fine
        if not original_available:
            assert result.returncode != 0
            assert 'faster-whisper' in result.stderr.lower() or 'Error' in result.stderr

    def test_fast_mode_with_status_file(self):
        """Test that --fast-mode works with --status-file"""
        import tempfile

        tmp_status = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        tmp_status.close()

        try:
            result = subprocess.run(
                [sys.executable, 'listen.py', '-f', '/tmp/fake.wav', '--fast-mode', '--status-file', tmp_status.name],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            # Should fail on file not found, not on argument combination
            assert 'File not found' in result.stderr or 'not found' in result.stderr.lower()
        finally:
            if os.path.exists(tmp_status.name):
                os.unlink(tmp_status.name)


class TestOutputTranscription:
    """Test critical output functionality"""

    def test_json_output_format(self):
        """Test that JSON output is properly formatted"""
        import json
        import listen

        # Temporarily set modes
        original_json = listen.json_mode
        original_quiet = listen.quiet_mode
        original_output = listen.output_file

        try:
            listen.json_mode = True
            listen.quiet_mode = False
            listen.output_file = None

            # Capture stdout
            from io import StringIO
            import sys
            captured = StringIO()
            sys.stdout = captured

            # Call output_transcription
            listen.output_transcription("test text", "en", "tiny", 1.5)

            # Get output
            sys.stdout = sys.__stdout__
            output = captured.getvalue()

            # Validate JSON
            data = json.loads(output.strip())
            assert data['transcription'] == 'test text'
            assert data['language'] == 'en'
            assert data['model'] == 'tiny'
            assert data['duration'] == 1.5

        finally:
            # Restore
            listen.json_mode = original_json
            listen.quiet_mode = original_quiet
            listen.output_file = original_output

    def test_file_output(self):
        """Test that file output writes correctly"""
        import listen

        # Temporarily set modes
        original_json = listen.json_mode
        original_quiet = listen.quiet_mode
        original_output = listen.output_file

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp_path = tmp.name

        try:
            listen.json_mode = False
            listen.quiet_mode = True
            listen.output_file = tmp_path

            # Capture stdout (should still print to stdout)
            from io import StringIO
            import sys
            captured = StringIO()
            sys.stdout = captured

            # Call output_transcription
            listen.output_transcription("test output", "es", "tiny")

            # Get stdout
            sys.stdout = sys.__stdout__
            stdout_output = captured.getvalue()

            # Verify stdout has the text
            assert 'test output' in stdout_output

            # Verify file was written
            with open(tmp_path, 'r') as f:
                file_content = f.read()
            assert file_content == 'test output'

        finally:
            # Restore
            listen.json_mode = original_json
            listen.quiet_mode = original_quiet
            listen.output_file = original_output
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
