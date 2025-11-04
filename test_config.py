#!/usr/bin/env python3
"""
Tests for config.py module
"""

import pytest
import tempfile
import os
import json
import config


@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create a temporary config directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = os.path.join(tmpdir, '.listen')
        config_file = os.path.join(config_dir, 'config.json')

        # Mock the config path functions
        monkeypatch.setattr(config, 'get_config_path', lambda: config_file)

        yield config_dir, config_file


class TestConfigDefaults:
    """Test default configuration values"""

    def test_get_defaults(self):
        """Test that defaults are properly structured"""
        defaults = config.get_defaults()

        assert defaults['language'] == 'en'
        assert defaults['model'] == 'base'
        assert defaults['claude'] is False
        assert defaults['verbose'] is False
        assert defaults['signal_mode'] is False

        # Test VAD defaults
        assert 'vad' in defaults
        assert defaults['vad']['enabled'] is False
        assert defaults['vad']['silence_duration'] == 2.0
        assert defaults['vad']['threshold'] == 0.015

        # Test server defaults
        assert 'server' in defaults
        assert defaults['server']['enabled'] is False
        assert defaults['server']['host'] == '0.0.0.0'
        assert defaults['server']['port'] == 5000

        # Test audio defaults
        assert 'audio' in defaults
        assert defaults['audio']['sample_rate'] == 16000
        assert defaults['audio']['channels'] == 1
        assert defaults['audio']['dtype'] == 'float32'


class TestConfigLoadSave:
    """Test loading and saving configuration"""

    def test_load_config_no_file(self, temp_config_dir):
        """Test loading config when file doesn't exist returns defaults"""
        config_dir, config_file = temp_config_dir

        loaded = config.load_config()
        defaults = config.get_defaults()

        assert loaded == defaults

    def test_save_and_load_config(self, temp_config_dir):
        """Test saving and loading configuration"""
        config_dir, config_file = temp_config_dir

        test_config = {
            'language': 'es',
            'model': 'tiny',
            'claude': True,
            'verbose': True,
            'signal_mode': False,
            'vad': {
                'enabled': True,
                'silence_duration': 3.0,
                'threshold': 0.02
            },
            'server': {
                'enabled': False,
                'host': '127.0.0.1',
                'port': 8080
            },
            'audio': {
                'sample_rate': 16000,
                'channels': 1,
                'dtype': 'float32'
            }
        }

        # Save config
        assert config.save_config(test_config) is True
        assert os.path.exists(config_file)

        # Load config
        loaded = config.load_config()
        assert loaded['language'] == 'es'
        assert loaded['model'] == 'tiny'
        assert loaded['claude'] is True
        assert loaded['vad']['enabled'] is True
        assert loaded['vad']['silence_duration'] == 3.0
        assert loaded['server']['port'] == 8080

    def test_load_invalid_json(self, temp_config_dir, capsys):
        """Test loading invalid JSON file"""
        config_dir, config_file = temp_config_dir

        # Create invalid JSON
        os.makedirs(config_dir, exist_ok=True)
        with open(config_file, 'w') as f:
            f.write('{ invalid json }')

        # Should return defaults and print warning
        loaded = config.load_config()
        defaults = config.get_defaults()

        assert loaded == defaults

        # Check warning was printed
        captured = capsys.readouterr()
        assert 'Warning' in captured.err or 'warning' in captured.err.lower()


class TestConfigMerging:
    """Test configuration merging logic"""

    def test_deep_merge_simple(self):
        """Test simple deep merge"""
        base = {'a': 1, 'b': 2}
        overlay = {'b': 3, 'c': 4}

        result = config.deep_merge(base, overlay)

        assert result == {'a': 1, 'b': 3, 'c': 4}

    def test_deep_merge_nested(self):
        """Test nested dictionary merge"""
        base = {
            'a': 1,
            'nested': {
                'x': 10,
                'y': 20
            }
        }
        overlay = {
            'a': 2,
            'nested': {
                'y': 30,
                'z': 40
            }
        }

        result = config.deep_merge(base, overlay)

        assert result['a'] == 2
        assert result['nested']['x'] == 10
        assert result['nested']['y'] == 30
        assert result['nested']['z'] == 40

    def test_merge_config_precedence(self):
        """Test that merge_config respects precedence: CLI > file > defaults"""
        defaults = {
            'language': 'en',
            'model': 'base',
            'vad': {'enabled': False}
        }

        file_config = {
            'language': 'es',
            'vad': {'enabled': True}
        }

        cli_args = {
            'model': 'tiny'
        }

        result = config.merge_config(defaults, file_config, cli_args)

        # CLI arg should override
        assert result['model'] == 'tiny'
        # File config should override defaults
        assert result['language'] == 'es'
        assert result['vad']['enabled'] is True


class TestConfigValidation:
    """Test configuration validation"""

    def test_validate_valid_config(self):
        """Test validation of a valid config"""
        valid_config = config.get_defaults()
        is_valid, error = config.validate_config(valid_config)

        assert is_valid is True
        assert error is None

    def test_validate_invalid_model(self):
        """Test validation fails for invalid model"""
        invalid_config = config.get_defaults()
        invalid_config['model'] = 'invalid_model'

        is_valid, error = config.validate_config(invalid_config)

        assert is_valid is False
        assert 'model' in error

    def test_validate_invalid_port(self):
        """Test validation fails for invalid port"""
        invalid_config = config.get_defaults()
        invalid_config['server']['port'] = 99999

        is_valid, error = config.validate_config(invalid_config)

        assert is_valid is False
        assert 'port' in error

    def test_validate_invalid_boolean(self):
        """Test validation fails for non-boolean values"""
        invalid_config = config.get_defaults()
        invalid_config['claude'] = 'true'  # String instead of boolean

        is_valid, error = config.validate_config(invalid_config)

        assert is_valid is False
        assert 'claude' in error

    def test_validate_invalid_vad_duration(self):
        """Test validation fails for invalid VAD duration"""
        invalid_config = config.get_defaults()
        invalid_config['vad']['silence_duration'] = 'not_a_number'

        is_valid, error = config.validate_config(invalid_config)

        assert is_valid is False
        assert 'silence_duration' in error


class TestConfigReset:
    """Test config reset functionality"""

    def test_reset_existing_config(self, temp_config_dir):
        """Test resetting an existing config file"""
        config_dir, config_file = temp_config_dir

        # Create a config file
        test_config = config.get_defaults()
        test_config['language'] = 'es'
        config.save_config(test_config)

        assert os.path.exists(config_file)

        # Reset config
        assert config.reset_config() is True
        assert not os.path.exists(config_file)

    def test_reset_nonexistent_config(self, temp_config_dir):
        """Test resetting when config doesn't exist"""
        config_dir, config_file = temp_config_dir

        # Should succeed even if file doesn't exist
        assert config.reset_config() is True


class TestConfigDisplay:
    """Test config display formatting"""

    def test_format_config_for_display(self):
        """Test config is properly formatted for display"""
        test_config = config.get_defaults()
        formatted = config.format_config_for_display(test_config)

        # Check it contains expected values
        assert 'language: en' in formatted
        assert 'model: base' in formatted
        assert 'VAD' in formatted
        assert 'Server:' in formatted
        assert 'Audio:' in formatted

        # Check formatting
        assert '\n' in formatted
        assert ':' in formatted
