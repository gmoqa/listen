# listen

minimal audio transcription tool

100% on-premise, no data sent to cloud

## install

### homebrew (recommended for mac)
```sh
brew tap gmoqa/listen
brew install listen
```

### one-liner (no homebrew needed)
```sh
curl -sSL https://raw.githubusercontent.com/gmoqa/listen/main/install.sh | bash
```

### arch linux
```sh
yay -S listen
```

## usage

```sh
listen              # record and transcribe (english)
listen -l es        # spanish
listen -m medium    # better model
```

press SPACE to stop recording

## models

- tiny
- base (default)
- small
- medium
- large

## uninstall

```sh
rm -rf ~/.local/share/listen ~/.local/bin/listen
```

all processing happens locally on your device
