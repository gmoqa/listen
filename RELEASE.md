# Release Process

This document describes how to release a new version of `listen`.

## Prerequisites

- Git with push access to `gmoqa/listen` and `gmoqa/homebrew-listen`
- `makepkg` installed (for AUR package updates) - optional, can be done manually
- Clean working directory (no uncommitted changes)

## Quick Release

```bash
./release.sh 1.2.0 "Add new feature X"
```

This will automatically:
1. Create and push git tag `v1.2.0`
2. Download tarball and calculate SHA256
3. Update `PKGBUILD` and `.SRCINFO` (AUR)
4. Update `listen.rb` (Homebrew)
5. Commit and push all changes

## Manual Release

If you prefer to do it step by step:

### 1. Create Git Tag

```bash
git tag -a v1.2.0 -m "Release v1.2.0 - Add feature X"
git push origin v1.2.0
```

### 2. Calculate SHA256

```bash
curl -sL https://github.com/gmoqa/listen/archive/refs/tags/v1.2.0.tar.gz -o listen.tar.gz
shasum -a 256 listen.tar.gz
```

### 3. Update AUR Package

Edit `PKGBUILD`:
```bash
pkgver=1.2.0
pkgrel=1
sha256sums=('NEW_SHA256_HERE')
```

Generate `.SRCINFO`:
```bash
makepkg --printsrcinfo > .SRCINFO
```

Commit:
```bash
git add PKGBUILD .SRCINFO
git commit -m "Bump version to 1.2.0"
git push origin main
```

### 4. Update Homebrew Formula

Edit `../homebrew-listen/listen.rb`:
```ruby
url "https://github.com/gmoqa/listen/archive/refs/tags/v1.2.0.tar.gz"
sha256 "NEW_SHA256_HERE"
```

Commit:
```bash
cd ../homebrew-listen
git add listen.rb
git commit -m "Bump version to 1.2.0"
git push origin main
```

## Environment Variables

- `HOMEBREW_LISTEN_PATH`: Path to homebrew-listen repo (default: `../homebrew-listen`)

```bash
export HOMEBREW_LISTEN_PATH=/path/to/homebrew-listen
./release.sh 1.2.0
```

## Troubleshooting

### Script fails with "makepkg not found"

The script will continue but skip `.SRCINFO` generation. Generate it manually:

```bash
makepkg --printsrcinfo > .SRCINFO
git add .SRCINFO
git commit --amend --no-edit
git push origin main
```

### Homebrew repo not found

The script will prompt you for the path or skip it. You can:
1. Set `HOMEBREW_LISTEN_PATH` environment variable
2. Update manually following step 4 above

### Wrong SHA256

If the checksum doesn't match, wait a few seconds for GitHub to process the release and try again.

## Post-Release

Users can update with:
- **Homebrew**: `brew upgrade listen`
- **AUR**: `yay -Syu listen`
- **Manual**: `curl -sSL https://raw.githubusercontent.com/gmoqa/listen/main/install.sh | bash`

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **Major** (1.0.0 → 2.0.0): Breaking changes
- **Minor** (1.0.0 → 1.1.0): New features, backward compatible
- **Patch** (1.0.0 → 1.0.1): Bug fixes

## Checklist

Before releasing:
- [ ] All tests pass
- [ ] README.md updated with new features
- [ ] CHANGELOG or commit messages are clear
- [ ] No uncommitted changes
- [ ] Version number follows semantic versioning
