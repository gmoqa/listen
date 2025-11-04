#!/usr/bin/env python3
import sys, os, tempfile, wave, time, threading, queue, fcntl, termios, re, signal
import config

# Lazy imports (loaded only when needed)
np = None
sd = None
whisper = None

# ANSI escape codes
CLR = '\033[K'
HOME = '\033[2J\033[H'
RED = '\033[91m'
YEL = '\033[93m'
MAG = '\033[95m'  # Magenta/Purple
RST = '\033[0m'

# Audio configuration
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'float32'

# VAD configuration
VAD_THRESHOLD = 0.015      # Volume threshold for silence detection
VAD_DEFAULT_DURATION = 2.0 # Default silence duration in seconds

# Server configuration
DEFAULT_SERVER_HOST = '0.0.0.0'
DEFAULT_SERVER_PORT = 5000

# Recording state
rec = []
lvl = [0.0]
pct = [0.0]
verbose = False
first_run = True
is_tty = sys.stdout.isatty()
stdin_is_tty = sys.stdin.isatty()
signal_stop = [False]
signal_mode = False
vad_enabled = False
vad_silence_duration = VAD_DEFAULT_DURATION
vad_threshold = VAD_THRESHOLD

def log(msg):
    if verbose:
        print(f'\n[DEBUG] {msg}', file=sys.stderr)


def signal_handler(signum, frame):
    """Handle SIGUSR1 to stop recording gracefully"""
    global signal_stop
    signal_stop[0] = True
    log(f'Received signal {signum}, stopping recording')


def audio_cb(data, frames, t, status):
    global np
    rec.append(data.copy())
    lvl[0] = float(np.sqrt(np.mean(data**2)))


def kbd_listen(q):
    if not stdin_is_tty:
        return

    try:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        flg = fcntl.fcntl(fd, fcntl.F_GETFL)
    except (termios.error, OSError):
        # Termux or environments where terminal control is not available
        log('Terminal control not available, keyboard listener disabled')
        return

    try:
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, new)
        fcntl.fcntl(fd, fcntl.F_SETFL, flg | os.O_NONBLOCK)

        while True:
            try:
                if sys.stdin.read(1) == ' ':
                    q.put(1)
                    break
            except (IOError, OSError, BlockingIOError):
                pass
            time.sleep(0.005)

        termios.tcsetattr(fd, termios.TCSAFLUSH, old)
        fcntl.fcntl(fd, fcntl.F_SETFL, flg)
    except Exception as e:
        log(f'Keyboard listener error: {e}')
        pass


def draw(c, bars, txt='Listening', hint=''):
    # Always show UI on stderr when not TTY (piped), or stdout when TTY
    out = sys.stderr if not is_tty else sys.stdout
    hint_str = f'  {MAG}{hint}{RST}' if hint else ''
    out.write(f'\r{RED}●{RST} {txt}  [{c}{bars}{RST}]{hint_str}')
    out.flush()


def record(start_proc):
    global rec, np, sd, signal_stop

    log('Loading audio libraries')
    if not np:
        import numpy
        np = numpy
        log('NumPy loaded')
    if not sd:
        import sounddevice
        sd = sounddevice
        log('SoundDevice loaded')

    rec = []
    q = queue.Queue()

    # Only start keyboard listener if not in signal mode
    if not signal_mode:
        log('Starting keyboard listener thread')
        threading.Thread(target=kbd_listen, args=(q,), daemon=True).start()

    # Determine hint message based on mode
    hint = ''
    if signal_mode:
        pid = os.getpid()
        hint = f'Signal mode: kill -SIGUSR1 {pid}'
    elif vad_enabled:
        hint = f'VAD mode: auto-stop after {vad_silence_duration}s silence'
    elif first_run and stdin_is_tty:
        hint = 'Press SPACE to stop'

    draw('', ' ' * 10, hint=hint)

    log(f'Starting audio stream ({SAMPLE_RATE//1000}kHz, {"stereo" if CHANNELS == 2 else "mono"})')
    # In signal mode or VAD mode, no timeout - wait for signal/silence
    # Otherwise, use timeout when piped (not TTY)
    timeout = None if (signal_mode or vad_enabled) else (10 if not stdin_is_tty else None)

    # VAD tracking variables
    silence_start = None
    has_speech = False

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, callback=audio_cb):
            t0 = time.time()
            while True:
                draw('', '=' * min(int(lvl[0] * 200), 10) + ' ' * max(10 - int(lvl[0] * 200), 0), hint=hint)

                # Check signal stop (for signal mode)
                if signal_mode and signal_stop[0]:
                    dur = time.time() - t0
                    log(f'Recording stopped by signal after {dur:.2f}s')
                    break

                # VAD: Check for silence
                if vad_enabled:
                    current_level = lvl[0]

                    # Detect if currently silent
                    is_silent = current_level < vad_threshold

                    if not is_silent:
                        # Speech detected
                        has_speech = True
                        silence_start = None
                        log(f'Speech detected (level: {current_level:.4f})')
                    elif has_speech:
                        # Silence after speech
                        if silence_start is None:
                            silence_start = time.time()
                            log(f'Silence started (level: {current_level:.4f})')
                        else:
                            silence_duration = time.time() - silence_start
                            if silence_duration >= vad_silence_duration:
                                dur = time.time() - t0
                                log(f'Recording stopped after {silence_duration:.2f}s of silence (total: {dur:.2f}s)')
                                break

                # Check timeout when piped
                if timeout and (time.time() - t0) >= timeout:
                    log(f'Recording stopped after timeout ({timeout}s)')
                    break

                # Check keyboard input (only if not in signal mode)
                if not signal_mode:
                    try:
                        if q.get_nowait():
                            dur = time.time() - t0
                            log(f'Recording stopped after {dur:.2f}s')
                            break
                    except queue.Empty:
                        pass

                time.sleep(0.05)
    except Exception as e:
        log(f'Error during recording: {e}')
        print(f'\n{e}', file=sys.stderr)
        return None

    for _ in range(3):
        draw('', '=' * 10)
        time.sleep(0.15)
        draw('', ' ' * 10)
        time.sleep(0.15)

    start_proc()

    if rec:
        frames = len(rec)
        log(f'Concatenating {frames} audio frames')
        data = np.concatenate(rec)
        if data.ndim > 1:
            data = data.flatten()
        return data
    else:
        log('No audio recorded')
        return None


def transcribe(path, model, lang, run=None, blink_state=None):
    global whisper, pct

    log(f'Loading Whisper model: {model}')
    if not whisper:
        import whisper as w
        whisper = w
        log('Whisper library loaded')

    try:
        t0 = time.time()
        m = whisper.load_model(model)
        log(f'Model loaded in {time.time()-t0:.2f}s')

        if blink_state:
            while (blink_state[0] // 6) % 2 != 0:
                time.sleep(0.01)
            pct[0] = 0.2

        class P:
            def write(self, txt):
                if verbose and txt.strip():
                    print(f'[WHISPER] {txt.strip()}', file=sys.__stderr__)
                if '%' in txt and (x := re.search(r'(\d+)%', txt)):
                    if blink_state:
                        pct[0] = 0.2 + int(x.group(1)) / 100.0 * 0.8
            def flush(self): pass

        old = sys.stderr
        sys.stderr = P()

        log(f'Starting transcription (language={lang})')
        t0 = time.time()
        r = m.transcribe(path, language=lang, fp16=False, verbose=False)
        log(f'Transcription completed in {time.time()-t0:.2f}s')
        log(f'Detected language: {r.get("language", "unknown")}')
        log(f'Text length: {len(r["text"])} chars')

        sys.stderr = old
        if blink_state:
            pct[0] = 1.0
            time.sleep(0.1)
    finally:
        time.sleep(0.05)

    return r


def start_server(host=DEFAULT_SERVER_HOST, port=DEFAULT_SERVER_PORT, model='base', lang='en'):
    """Start Flask server for audio transcription API"""
    global whisper, verbose

    # Lazy import - only load Flask if server mode is used
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print('Error: Flask is required for server mode', file=sys.stderr)
        print('Install: pip install flask', file=sys.stderr)
        sys.exit(1)

    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok'})

    @app.route('/transcribe', methods=['POST'])
    def transcribe_audio():
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get optional parameters
        req_lang = request.form.get('language', lang)
        req_model = request.form.get('model', model)

        # Save uploaded file to temp location
        tmp = tempfile.NamedTemporaryFile(suffix='.audio', delete=False)
        try:
            audio_file.save(tmp.name)
            tmp.close()

            log(f'Received file: {audio_file.filename} ({os.path.getsize(tmp.name)} bytes)')
            log(f'Transcribing with model={req_model}, language={req_lang}')

            # Transcribe without UI elements (no run/blink_state)
            result = transcribe(tmp.name, req_model, req_lang)

            return jsonify({
                'text': result['text'].strip(),
                'language': result.get('language', req_lang)
            })
        except Exception as e:
            log(f'Transcription error: {e}')
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                os.unlink(tmp.name)
            except:
                pass

    print(f'Starting transcription API server on {host}:{port}')
    print(f'Model: {model}, Language: {lang}')
    print(f'\nEndpoints:')
    print(f'  GET  /health     - Health check')
    print(f'  POST /transcribe - Transcribe audio file')
    print(f'\nExample usage:')
    print(f'  curl -X POST -F "audio=@file.mp3" http://{host}:{port}/transcribe')
    print(f'\nPress Ctrl+C to stop the server\n')

    app.run(host=host, port=port, debug=False)


def handle_config_command(args):
    """Handle 'listen config' subcommand"""
    if not args or args[0] in ['-h', '--help']:
        config.show_config_help()
        return 0

    # Check for special commands first
    if '--show' in args:
        current_config = config.load_config()
        print(config.format_config_for_display(current_config))
        return 0

    if '--reset' in args:
        if config.reset_config():
            print('Configuration reset to defaults')
            print(f'Config file deleted: {config.get_config_path()}')
            return 0
        else:
            print('Error: Could not reset configuration', file=sys.stderr)
            return 1

    # Load current config
    current_config = config.load_config()
    changes = {}

    # Parse arguments to update
    i = 0
    while i < len(args):
        arg = args[i]

        if arg in ['-l', '--language']:
            if i + 1 >= len(args):
                print('Error: --language requires an argument', file=sys.stderr)
                return 1
            changes['language'] = args[i + 1]
            i += 2

        elif arg in ['-m', '--model']:
            if i + 1 >= len(args):
                print('Error: --model requires an argument', file=sys.stderr)
                return 1
            model = args[i + 1]
            if model not in ['tiny', 'base', 'small', 'medium', 'large']:
                print(f'Error: Invalid model "{model}". Must be: tiny, base, small, medium, large', file=sys.stderr)
                return 1
            changes['model'] = model
            i += 2

        elif arg == '--vad':
            if i + 1 >= len(args):
                print('Error: --vad requires a number (seconds)', file=sys.stderr)
                return 1
            try:
                duration = float(args[i + 1])
                if duration <= 0:
                    print('Error: --vad must be a positive number', file=sys.stderr)
                    return 1
                if 'vad' not in changes:
                    changes['vad'] = current_config.get('vad', {}).copy()
                changes['vad']['enabled'] = True
                changes['vad']['silence_duration'] = duration
            except ValueError:
                print(f'Error: Invalid number for --vad: {args[i + 1]}', file=sys.stderr)
                return 1
            i += 2

        elif arg == '--host':
            if i + 1 >= len(args):
                print('Error: --host requires an argument', file=sys.stderr)
                return 1
            if 'server' not in changes:
                changes['server'] = current_config.get('server', {}).copy()
            changes['server']['host'] = args[i + 1]
            i += 2

        elif arg == '--port':
            if i + 1 >= len(args):
                print('Error: --port requires a number', file=sys.stderr)
                return 1
            try:
                port = int(args[i + 1])
                if not (1 <= port <= 65535):
                    print('Error: Port must be between 1 and 65535', file=sys.stderr)
                    return 1
                if 'server' not in changes:
                    changes['server'] = current_config.get('server', {}).copy()
                changes['server']['port'] = port
            except ValueError:
                print(f'Error: Invalid port number: {args[i + 1]}', file=sys.stderr)
                return 1
            i += 2

        elif arg == '--claude':
            # Toggle claude mode
            current_claude = current_config.get('claude', False)
            changes['claude'] = not current_claude
            i += 1

        elif arg == '--verbose':
            # Toggle verbose mode
            current_verbose = current_config.get('verbose', False)
            changes['verbose'] = not current_verbose
            i += 1

        elif arg == '--signal-mode':
            # Toggle signal mode
            current_signal = current_config.get('signal_mode', False)
            changes['signal_mode'] = not current_signal
            i += 1

        else:
            print(f'Error: Unknown config option: {arg}', file=sys.stderr)
            print('Run "listen config --help" for usage', file=sys.stderr)
            return 1

    # If no changes, show help
    if not changes:
        config.show_config_help()
        return 0

    # Apply changes to current config
    updated_config = config.deep_merge(current_config, changes)

    # Validate
    is_valid, error = config.validate_config(updated_config)
    if not is_valid:
        print(f'Error: {error}', file=sys.stderr)
        return 1

    # Save
    if config.save_config(updated_config):
        print('Configuration updated successfully')
        print(f'Saved to: {config.get_config_path()}')
        print()
        print('Changes:')
        for key, value in changes.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    print(f'  {key}.{subkey}: {subvalue}')
            else:
                print(f'  {key}: {value}')
        return 0
    else:
        print('Error: Could not save configuration', file=sys.stderr)
        return 1


def main():
    global verbose, first_run, signal_mode, vad_enabled, vad_silence_duration

    # Check if this is a config subcommand
    if len(sys.argv) > 1 and sys.argv[1] == 'config':
        sys.exit(handle_config_command(sys.argv[2:]))

    # Handle help before config loading
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("usage: listen [config|COMMAND] [OPTIONS]")
        print("\nCommands:")
        print("  config              Manage persistent configuration")
        print("\nModes:")
        print("  (default)           Record audio from microphone and transcribe")
        print("  -s, --server        Start HTTP API server for transcription")
        print("  -f, --file FILE     Transcribe audio from file (mp3, wav, m4a, etc.)")
        print("\nOptions:")
        print("  -l, --language LANG     Language code (default: from config or 'en')")
        print("  -m, --model MODEL       Whisper model (default: from config or 'base')")
        print("  -c, --claude            Send transcription to Claude")
        print("  --signal-mode           Use SIGUSR1 signal to stop recording")
        print("  --vad SECONDS           Auto-stop after N seconds of silence")
        print("  -v, --verbose           Verbose output")
        print("\nServer options:")
        print(f"  --host HOST             Server host (default: {DEFAULT_SERVER_HOST})")
        print(f"  --port PORT             Server port (default: {DEFAULT_SERVER_PORT})")
        print("\nRecording controls:")
        print("  (default) Press SPACE to stop recording")
        print("  (signal)  Send SIGUSR1 to process (kill -SIGUSR1 <pid>)")
        print("  (vad)     Auto-stop after silence duration")
        print("\nConfiguration:")
        print("  Config file: ~/.listen/config.json")
        print("  Precedence: CLI args > config file > defaults")
        print("  See 'listen config --help' for config management")
        return

    marker = os.path.expanduser('~/.local/share/listen/.first_run_done')
    if os.path.exists(marker):
        first_run = False
    else:
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        with open(marker, 'w') as f:
            f.write('')

    # Clear screen on the appropriate stream
    out = sys.stderr if not is_tty else sys.stdout
    out.write(HOME)
    out.flush()

    # Parse CLI arguments (only explicitly provided ones)
    cli_args = {}
    file_path = None
    i = 0
    args = sys.argv[1:]

    while i < len(args):
        arg = args[i]

        if arg in ['-l', '--language'] and i + 1 < len(args):
            cli_args['language'] = args[i + 1]
            i += 2
        elif arg in ['-m', '--model'] and i + 1 < len(args):
            cli_args['model'] = args[i + 1]
            i += 2
        elif arg in ['-c', '--claude']:
            cli_args['claude'] = True
            i += 1
        elif arg in ['-s', '--server']:
            if 'server' not in cli_args:
                cli_args['server'] = {}
            cli_args['server']['enabled'] = True
            i += 1
        elif arg in ['-f', '--file'] and i + 1 < len(args):
            file_path = args[i + 1]
            i += 2
        elif arg == '--signal-mode':
            cli_args['signal_mode'] = True
            i += 1
        elif arg == '--vad' and i + 1 < len(args):
            if 'vad' not in cli_args:
                cli_args['vad'] = {}
            cli_args['vad']['enabled'] = True
            cli_args['vad']['silence_duration'] = float(args[i + 1])
            i += 2
        elif arg == '--host' and i + 1 < len(args):
            if 'server' not in cli_args:
                cli_args['server'] = {}
            cli_args['server']['host'] = args[i + 1]
            i += 2
        elif arg == '--port' and i + 1 < len(args):
            if 'server' not in cli_args:
                cli_args['server'] = {}
            cli_args['server']['port'] = int(args[i + 1])
            i += 2
        elif arg in ['-v', '--verbose']:
            cli_args['verbose'] = True
            i += 1
        else:
            i += 1

    # Load config and merge with CLI args
    defaults = config.get_defaults()
    file_config = config.load_config()
    final_config = config.merge_config(defaults, file_config, cli_args)

    # Extract values from merged config
    lang = final_config['language']
    mdl = final_config['model']
    use_claude = final_config['claude']
    verbose = final_config['verbose']
    signal_mode = final_config['signal_mode']

    # VAD settings
    vad_enabled = final_config['vad']['enabled']
    vad_silence_duration = final_config['vad']['silence_duration']

    # Server settings
    server_mode = final_config['server']['enabled']
    server_host = final_config['server']['host']
    server_port = final_config['server']['port']

    # Server mode
    if server_mode:
        start_server(host=server_host, port=server_port, model=mdl, lang=lang)
        return

    # File mode - transcribe from file
    if file_path:
        # Validate file exists
        if not os.path.exists(file_path):
            print(f'Error: File not found: {file_path}', file=sys.stderr)
            sys.exit(1)

        # Validate file is readable
        if not os.path.isfile(file_path):
            print(f'Error: Not a file: {file_path}', file=sys.stderr)
            sys.exit(1)

        # Check file size (warn if > 100MB)
        file_size = os.path.getsize(file_path)
        if file_size > 100 * 1024 * 1024:
            print(f'Warning: Large file ({file_size / (1024*1024):.1f}MB), transcription may take a while', file=sys.stderr)

        log(f'Processing file: {file_path} ({file_size} bytes)')

        # Show processing UI
        global pct
        run = [True]
        blink_state = [0]

        def start_proc():
            def prog():
                while run[0]:
                    n = int(pct[0] * 10)
                    if pct[0] < 0.15:
                        bars = ('=' if (blink_state[0] // 6) % 2 == 0 else ' ') + ' ' * 9
                    else:
                        bars = '=' * max(1, n) + ' ' * (10 - max(1, n))
                    blink_state[0] += 1
                    draw(YEL, bars, 'Processing')
                    time.sleep(0.05)
            threading.Thread(target=prog, daemon=True).start()
            pct[0] = 0.0

        start_proc()

        try:
            r = transcribe(file_path, mdl, lang, run, blink_state)
            # Clear the UI line
            out = sys.stderr if not is_tty else sys.stdout
            out.write('\r' + CLR)
            out.flush()
            log(f'Final transcription: "{r["text"].strip()}"')

            text = r['text'].strip()

            if use_claude:
                # Send transcribed text as prompt to claude
                import subprocess
                import shlex
                log(f'Sending to claude as prompt: "{text}"')

                # Try common claude paths
                claude_path = os.path.expanduser('~/.claude/local/claude')
                if not os.path.exists(claude_path):
                    claude_path = 'claude'

                try:
                    cmd = f'{claude_path} -p {shlex.quote(text)}'
                    subprocess.run(cmd, shell=True, check=True)
                except subprocess.CalledProcessError as e:
                    print(f'Error running claude: {e}', file=sys.stderr)
                    sys.exit(1)
            else:
                print(text, flush=True)
        except Exception as e:
            log(f'Transcription error: {e}')
            print(f'Error: {e}', file=sys.stderr)
            sys.exit(1)
        finally:
            run[0] = False

        return

    # Configure signal handler if in signal mode
    if signal_mode:
        signal.signal(signal.SIGUSR1, signal_handler)
        log('Signal mode enabled: listening for SIGUSR1')

    log(f'Starting listen (language={lang}, model={mdl})')

    global pct
    run = [True]
    blink_state = [0]

    def start_proc():
        def prog():
            while run[0]:
                n = int(pct[0] * 10)
                if pct[0] < 0.15:
                    bars = ('=' if (blink_state[0] // 6) % 2 == 0 else ' ') + ' ' * 9
                else:
                    bars = '=' * max(1, n) + ' ' * (10 - max(1, n))
                blink_state[0] += 1
                draw(YEL, bars, 'Processing')
                time.sleep(0.05)
        threading.Thread(target=prog, daemon=True).start()
        pct[0] = 0.0

    data = record(start_proc)
    if data is None or len(data) == 0:
        log('No audio data to process')
        sys.exit(1)

    log(f'Audio data shape: {data.shape}, duration: {len(data)/SAMPLE_RATE:.2f}s')

    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    log(f'Saving audio to temp file: {tmp.name}')
    with wave.open(tmp.name, 'wb') as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes((data * 32767).astype(np.int16).tobytes())
    log(f'Audio file size: {os.path.getsize(tmp.name)} bytes')

    try:
        r = transcribe(tmp.name, mdl, lang, run, blink_state)
        # Clear the UI line on the appropriate stream
        out = sys.stderr if not is_tty else sys.stdout
        out.write('\r' + CLR)
        out.flush()
        log(f'Final transcription: "{r["text"].strip()}"')

        text = r['text'].strip()

        if use_claude:
            # Send transcribed text as prompt to claude
            import subprocess
            import shlex
            log(f'Sending to claude as prompt: "{text}"')

            # Try common claude paths
            claude_path = os.path.expanduser('~/.claude/local/claude')
            if not os.path.exists(claude_path):
                claude_path = 'claude'

            try:
                # Use shell=True to support aliases, properly escape text
                cmd = f'{claude_path} -p {shlex.quote(text)}'
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f'Error running claude: {e}', file=sys.stderr)
                sys.exit(1)
        else:
            print(text, flush=True)
    except Exception as e:
        log(f'Transcription error: {e}')
        sys.exit(1)
    finally:
        run[0] = False
        try:
            os.unlink(tmp.name)
            log(f'Deleted temp file: {tmp.name}')
        except:
            pass


if __name__ == '__main__':
    main()
