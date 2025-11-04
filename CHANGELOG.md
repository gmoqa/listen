# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.2.2] - 2025-01-04

### Fixed
- **Clean error handling** - No more ugly Python tracebacks
  - Show clean error messages by default
  - Full traceback available with `-v/--verbose` flag
  - Graceful handling of KeyboardInterrupt (Ctrl+C)

## [1.2.1] - 2025-01-04

### Added
- **Scripting mode flags** - Perfect for automation and workflows
  - `-q/--quiet` - Suppress UI, output only transcription text
  - `-j/--json` - Output in JSON format with metadata
  - `--clipboard` - Auto-copy transcription to clipboard (macOS/Linux/Windows)
  - `-o/--output FILE` - Write transcription to file
- Multi-platform clipboard support (macOS/Linux/Windows)
- Proper stdout/stderr separation for pipe-friendly output

### Changed
- Updated README with scripting/automation examples
- UI output now goes to stderr, transcription to stdout

## [1.2.0] - 2025-01-04

### Added
- **File transcription mode** (`-f/--file` flag) - Transcribe audio files directly without recording
  - Supports mp3, wav, m4a, flac, ogg, and other formats via ffmpeg
  - File validation and error handling
  - Large file warnings (>100MB)
- **Comprehensive test suite** using pytest
  - 27 tests covering config, CLI, file validation, and error handling
  - Test coverage reporting with pytest-cov
  - Automated test runner script (`run_tests.sh`)
  - CI-ready test infrastructure

### Changed
- Updated README with file processing examples
- Added development section with testing instructions
- Enhanced .gitignore for test artifacts

### Documentation
- Added SUCKLESS_REVIEW.md - Comprehensive suckless analysis
- Added SUCKLESS_SUMMARY.md - Executive summary of improvements
- Added SIMPLIFICATION_DEMO.md - Before/after code examples
- Added SUCKLESS_ROADMAP.md - Implementation roadmap
- Added SUCKLESS_INDEX.md - Navigation guide
- Added analyze_complexity.sh - Code metrics tool

### Fixed
- Improved error messages for file not found scenarios
- Better handling of edge cases in file processing

## [1.1.3] - Previous Release

### Added
- Improved first-run UX with inline hints
- Better user guidance for initial usage

## [1.1.2] - Previous Release

### Added
- Automated release script
- Release documentation

## [1.1.1] - Previous Release

### Initial Features
- Microphone recording and transcription
- Multiple Whisper model support (tiny, base, small, medium, large)
- Multi-language support
- Configuration management via JSON
- Server mode for HTTP API
- VAD (Voice Activity Detection) mode
- Signal mode for programmatic control
- Claude integration
- Verbose mode for debugging
