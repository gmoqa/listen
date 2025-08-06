#!/usr/bin/env python3
import sys, os, tempfile, wave, time, threading, queue, fcntl, termios, re

np = None
sd = None
whisper = None

CLR = '\033[K'
HOME = '\033[2J\033[H'
RED = '\033[91m'
YEL = '\033[93m'
RST = '\033[0m'

rec = []
lvl = [0.0]
pct = [0.0]


def audio_cb(data, frames, t, status):
    global np
    rec.append(data.copy())
    lvl[0] = float(np.sqrt(np.mean(data**2)))


def kbd_listen(q):
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    flg = fcntl.fcntl(fd, fcntl.F_GETFL)

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
    except:
        pass


def draw(c, bars):
    sys.stdout.write(f'\r{RED}●{RST} Listening  [{c}{bars}{RST}]')
    sys.stdout.flush()


def record(start_proc):
    global rec, np, sd

    if not np:
        import numpy
        np = numpy
    if not sd:
        import sounddevice
        sd = sounddevice

    rec = []
    q = queue.Queue()

    threading.Thread(target=kbd_listen, args=(q,), daemon=True).start()
    draw('', ' ' * 10)

    try:
        with sd.InputStream(samplerate=16000, channels=1, dtype='float32', callback=audio_cb):
            while True:
                draw('', '=' * min(int(lvl[0] * 200), 10) + ' ' * max(10 - int(lvl[0] * 200), 0))
                try:
                    if q.get_nowait():
                        break
                except queue.Empty:
                    pass
                time.sleep(0.05)
    except Exception as e:
        print(f'\n{e}', file=sys.stderr)
        return None

    for _ in range(3):
        draw('', '=' * 10)
        time.sleep(0.15)
        draw('', ' ' * 10)
        time.sleep(0.15)

    start_proc()

    return np.concatenate(rec) if rec else None


def transcribe(path, model, lang, run, blink_state):
    global whisper, pct

    if not whisper:
        import whisper as w
        whisper = w

    try:
        m = whisper.load_model(model)
        while (blink_state[0] // 6) % 2 != 0:
            time.sleep(0.01)
        pct[0] = 0.2

        class P:
            def write(self, txt):
                if '%' in txt and (x := re.search(r'(\d+)%', txt)):
                    pct[0] = 0.2 + int(x.group(1)) / 100.0 * 0.8
            def flush(self): pass

        old = sys.stderr
        sys.stderr = P()
        r = m.transcribe(path, language=lang, fp16=False, verbose=False)
        sys.stderr = old
        pct[0] = 1.0
        time.sleep(0.1)
    finally:
        time.sleep(0.05)

    return r


def main():
    sys.stdout.write(HOME)
    sys.stdout.flush()

    lang = 'en'
    mdl = 'base'

    for i, a in enumerate(sys.argv[1:]):
        if a in ['-l', '--language'] and i + 2 < len(sys.argv):
            lang = sys.argv[i + 2]
        elif a in ['-m', '--model'] and i + 2 < len(sys.argv):
            mdl = sys.argv[i + 2]
        elif a in ['-h', '--help']:
            print("usage: listen [-l LANG] [-m MODEL]\nPress SPACE to stop")
            return

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
                draw(YEL, bars)
                time.sleep(0.05)
        threading.Thread(target=prog, daemon=True).start()
        pct[0] = 0.0

    data = record(start_proc)
    if data is None or len(data) == 0:
        sys.exit(1)

    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    with wave.open(tmp.name, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes((data * 32767).astype(np.int16).tobytes())

    try:
        r = transcribe(tmp.name, mdl, lang, run, blink_state)
        sys.stdout.write('\r' + CLR)
        print(r['text'].strip())
    except:
        sys.exit(1)
    finally:
        run[0] = False
        try:
            os.unlink(tmp.name)
        except:
            pass


if __name__ == '__main__':
    main()
