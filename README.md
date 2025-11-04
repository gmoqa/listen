# listen

minimal audio transcription tool

## install

### homebrew (mac/linux)
```sh
brew tap gmoqa/listen
brew install listen
```

### termux (android)
```sh
# via package manager (coming soon - pending approval)
pkg install listen

# current install method (one-liner)
curl -sSL https://raw.githubusercontent.com/gmoqa/listen/main/install-termux.sh | bash
```

see [TERMUX.md](TERMUX.md) for detailed android setup

### arch linux
```sh
yay -S listen
```

### one-liner (generic linux/mac)
```sh
curl -sSL https://raw.githubusercontent.com/gmoqa/listen/main/install.sh | bash
```

## usage

### basic
```sh
listen              # record and transcribe (english)
listen -l es        # spanish
listen -m medium    # better model
listen -c           # send to claude
listen -v           # verbose mode
```

press SPACE to stop recording

### file processing
```sh
listen -f audio.mp3           # transcribe audio file
listen -f audio.wav -l es     # transcribe with language
listen -f audio.m4a -m medium # transcribe with better model
listen -f audio.mp3 -c        # transcribe and send to claude
```

supports: mp3, wav, m4a, flac, ogg, and other formats supported by ffmpeg

### configuration

**set defaults (persistent)**
```sh
listen config -l es         # set spanish as default language
listen config -m tiny       # set tiny model as default
listen config --vad 3       # enable VAD with 3s silence
listen config --show        # view current config
listen config --reset       # delete config file
```

configuration is saved to `~/.listen/config.json`

**precedence**: CLI args > config file > defaults

```sh
listen config -l es -m tiny  # save defaults
listen                       # uses: es, tiny (from config)
listen -l en                 # uses: en (override), tiny (from config)
```

### advanced modes

**auto-stop with silence detection**
```sh
listen --vad 2      # stop after 2s of silence
```

**signal control (for scripts)**
```sh
listen --signal-mode &
kill -SIGUSR1 $(pgrep -f "listen.*signal")
```

**http api server**
```sh
listen -s                              # start server on :5000
listen -s --port 8080 --host 127.0.0.1
curl -X POST -F "audio=@file.mp3" http://localhost:5000/transcribe
```

## models

- tiny
- base (default)
- small
- medium
- large

## platform notes

### termux (android)

**microphone permissions**
```sh
# grant storage and microphone permissions
termux-setup-storage
# allow microphone when prompted
```

**recommended models for mobile**
- `tiny` - fastest, lowest memory (~1GB RAM)
- `base` - balanced (default, ~2GB RAM)
- avoid `medium`/`large` on phones (high memory usage)

**troubleshooting**
```sh
# if audio fails, try:
pkg install pulseaudio
pulseaudio --start

# check microphone access
termux-microphone-record -f test.wav -l 1
termux-microphone-record -q
```

## development

### running tests

**quick start**
```sh
./run_tests.sh              # run all tests
./run_tests.sh quick        # quick run (minimal output)
./run_tests.sh coverage     # run with coverage report
./run_tests.sh config       # run only config tests
./run_tests.sh listen       # run only listen tests
```

**using pytest directly**
```sh
# run all tests
pytest

# run with coverage report
pytest --cov=. --cov-report=html

# run specific test file
pytest test_config.py -v

# run specific test class
pytest test_config.py::TestConfigDefaults -v

# run specific test
pytest test_config.py::TestConfigDefaults::test_get_defaults -v
```

### test structure
- `test_config.py` - tests for configuration management
- `test_listen.py` - tests for CLI and main functionality
- `conftest.py` - shared fixtures and test utilities
- `pytest.ini` - pytest configuration

### coverage
view coverage report after running tests with `--cov-report=html`:
```sh
open htmlcov/index.html  # mac
xdg-open htmlcov/index.html  # linux
```

## uninstall

**termux**
```sh
rm $PREFIX/bin/listen
pip uninstall openai-whisper sounddevice numpy scipy
```

**mac/linux**
```sh
rm -rf ~/.local/share/listen ~/.local/bin/listen
```

all processing happens locally on your device
