#!/usr/bin/env python3
"""
Configuration management for listen CLI tool.

Handles loading, saving, and merging configuration from:
1. CLI arguments (highest priority)
2. Config file (~/.listen/config.json)
3. Hardcoded defaults (lowest priority)
"""

import os
import json
import sys


def get_config_path():
    """Return path to config file: ~/.listen/config.json"""
    home = os.path.expanduser('~')
    config_dir = os.path.join(home, '.listen')
    return os.path.join(config_dir, 'config.json')


def ensure_config_dir():
    """Create ~/.listen/ directory if it doesn't exist"""
    config_path = get_config_path()
    config_dir = os.path.dirname(config_path)

    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir, mode=0o755)
        except OSError as e:
            print(f'Warning: Could not create config directory: {e}', file=sys.stderr)
            return False
    return True


def get_defaults():
    """Return default configuration dictionary"""
    return {
        'language': 'en',
        'model': 'base',
        'claude': False,
        'verbose': False,
        'signal_mode': False,
        'codevoice': False,
        'vad': {
            'enabled': False,
            'silence_duration': 2.0,
            'threshold': 0.015
        },
        'server': {
            'enabled': False,
            'host': '0.0.0.0',
            'port': 5000
        },
        'audio': {
            'sample_rate': 16000,
            'channels': 1,
            'dtype': 'float32'
        }
    }


def load_config():
    """Load configuration from file, or return defaults if not exists"""
    config_path = get_config_path()

    if not os.path.exists(config_path):
        return get_defaults()

    try:
        with open(config_path, 'r') as f:
            file_config = json.load(f)

        # Merge with defaults to ensure all keys exist
        defaults = get_defaults()
        merged = deep_merge(defaults, file_config)
        return merged

    except (json.JSONDecodeError, IOError) as e:
        print(f'Warning: Could not load config file: {e}', file=sys.stderr)
        print('Using default configuration', file=sys.stderr)
        return get_defaults()


def save_config(config):
    """Save configuration to JSON file"""
    if not ensure_config_dir():
        print('Error: Could not create config directory', file=sys.stderr)
        return False

    config_path = get_config_path()

    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        print(f'Error: Could not save config file: {e}', file=sys.stderr)
        return False


def deep_merge(base, overlay):
    """Deep merge two dictionaries, overlay takes precedence"""
    result = base.copy()

    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def merge_config(defaults, file_config, cli_args):
    """
    Merge three layers of configuration with proper precedence:
    CLI args > file config > defaults

    Args:
        defaults: Default configuration dict
        file_config: Configuration from ~/.listen/config.json
        cli_args: Arguments explicitly provided via CLI

    Returns:
        Merged configuration dict
    """
    # Start with defaults
    result = defaults.copy()

    # Apply file config
    result = deep_merge(result, file_config)

    # Apply CLI args (only keys that were explicitly provided)
    result = deep_merge(result, cli_args)

    return result


def validate_config(config):
    """
    Validate configuration values

    Returns:
        (bool, str): (is_valid, error_message)
    """
    # Validate language
    if not isinstance(config.get('language'), str):
        return False, 'language must be a string'

    # Validate model
    valid_models = ['tiny', 'base', 'small', 'medium', 'large']
    if config.get('model') not in valid_models:
        return False, f'model must be one of: {", ".join(valid_models)}'

    # Validate booleans
    for key in ['claude', 'verbose', 'signal_mode']:
        if not isinstance(config.get(key), bool):
            return False, f'{key} must be a boolean'

    # Validate VAD
    if 'vad' in config:
        if not isinstance(config['vad'].get('enabled'), bool):
            return False, 'vad.enabled must be a boolean'
        if not isinstance(config['vad'].get('silence_duration'), (int, float)):
            return False, 'vad.silence_duration must be a number'
        if not isinstance(config['vad'].get('threshold'), (int, float)):
            return False, 'vad.threshold must be a number'

    # Validate server
    if 'server' in config:
        if not isinstance(config['server'].get('enabled'), bool):
            return False, 'server.enabled must be a boolean'
        if not isinstance(config['server'].get('host'), str):
            return False, 'server.host must be a string'
        if not isinstance(config['server'].get('port'), int):
            return False, 'server.port must be an integer'
        if not (1 <= config['server']['port'] <= 65535):
            return False, 'server.port must be between 1 and 65535'

    return True, None


def update_config_key(key_path, value):
    """
    Update a single configuration key and save to file

    Args:
        key_path: Dot-separated path (e.g., 'language', 'vad.enabled', 'server.port')
        value: New value to set

    Returns:
        bool: True if successful
    """
    config = load_config()

    # Navigate to nested key
    keys = key_path.split('.')
    current = config

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set the value
    current[keys[-1]] = value

    # Validate
    is_valid, error = validate_config(config)
    if not is_valid:
        print(f'Error: Invalid configuration - {error}', file=sys.stderr)
        return False

    # Save
    return save_config(config)


def reset_config():
    """Delete config file, reverting to defaults"""
    config_path = get_config_path()

    if os.path.exists(config_path):
        try:
            os.remove(config_path)
            return True
        except OSError as e:
            print(f'Error: Could not delete config file: {e}', file=sys.stderr)
            return False
    return True  # Already doesn't exist


def format_config_for_display(config):
    """Pretty print configuration for display"""
    config_path = get_config_path()

    lines = [
        f'Configuration ({config_path}):',
        '',
        f'  language: {config["language"]}',
        f'  model: {config["model"]}',
        f'  claude: {str(config["claude"]).lower()}',
        f'  verbose: {str(config["verbose"]).lower()}',
        f'  signal_mode: {str(config["signal_mode"]).lower()}',
        '',
        '  VAD (Voice Activity Detection):',
        f'    enabled: {str(config["vad"]["enabled"]).lower()}',
        f'    silence_duration: {config["vad"]["silence_duration"]}s',
        f'    threshold: {config["vad"]["threshold"]}',
        '',
        '  Server:',
        f'    enabled: {str(config["server"]["enabled"]).lower()}',
        f'    host: {config["server"]["host"]}',
        f'    port: {config["server"]["port"]}',
        '',
        '  Audio:',
        f'    sample_rate: {config["audio"]["sample_rate"]} Hz',
        f'    channels: {config["audio"]["channels"]}',
        f'    dtype: {config["audio"]["dtype"]}',
    ]

    return '\n'.join(lines)


def show_config_help():
    """Display help for config subcommand"""
    help_text = '''Usage: listen config [OPTIONS]

Manage persistent configuration for listen CLI.

Options:
  -l, --language LANG    Set default language (e.g., en, es, fr)
  -m, --model MODEL      Set default model (tiny, base, small, medium, large)
  --vad SECONDS         Set default VAD silence duration
  --host HOST           Set default server host
  --port PORT           Set default server port
  --claude              Toggle claude mode (on/off)
  --verbose             Toggle verbose mode (on/off)
  --signal-mode         Toggle signal mode (on/off)
  --show                Display current configuration
  --reset               Delete config file (revert to defaults)

Examples:
  listen config -l es                 # Set default language to Spanish
  listen config -m tiny --vad 3       # Set model and VAD duration
  listen config --show                # View current config
  listen config --reset               # Delete config file

Config file location: ~/.listen/config.json

Precedence: CLI args > config file > built-in defaults
'''
    print(help_text)
