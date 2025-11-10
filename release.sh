#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if version argument provided
if [ -z "$1" ]; then
    error "Usage: ./release.sh <version> [release_notes]"
fi

VERSION="$1"
RELEASE_NOTES="${2:-Release version $VERSION}"

# Remove 'v' prefix if present
VERSION_NUM="${VERSION#v}"

info "Starting release process for version $VERSION_NUM"

# Verify we're in the listen repo
if [ ! -f "listen.py" ]; then
    error "Must be run from the listen repository root"
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    error "You have uncommitted changes. Please commit or stash them first."
fi

# Check if Homebrew repo path is set
HOMEBREW_REPO="${HOMEBREW_LISTEN_PATH:-../homebrew-listen}"
if [ ! -d "$HOMEBREW_REPO" ]; then
    warn "Homebrew repo not found at $HOMEBREW_REPO"
    read -p "Enter path to homebrew-listen repo (or skip with Enter): " custom_path
    if [ -n "$custom_path" ]; then
        HOMEBREW_REPO="$custom_path"
    else
        warn "Skipping Homebrew update"
        HOMEBREW_REPO=""
    fi
fi

# Check if AUR repo path is set
AUR_REPO="${AUR_LISTEN_PATH:-../listen-aur}"
if [ ! -d "$AUR_REPO" ]; then
    warn "AUR repo not found at $AUR_REPO"
    read -p "Enter path to listen-aur repo (or skip with Enter): " custom_path
    if [ -n "$custom_path" ]; then
        AUR_REPO="$custom_path"
    else
        warn "Skipping AUR sync"
        AUR_REPO=""
    fi
fi

info "Creating git tag v$VERSION_NUM"
git tag -a "v$VERSION_NUM" -m "$RELEASE_NOTES"

info "Pushing tag to remote"
git push origin "v$VERSION_NUM"

info "Calculating SHA256 checksum"
# Download the tarball from GitHub
TARBALL_URL="https://github.com/gmoqa/listen/archive/refs/tags/v$VERSION_NUM.tar.gz"
TEMP_DIR=$(mktemp -d)
curl -sL "$TARBALL_URL" -o "$TEMP_DIR/listen-$VERSION_NUM.tar.gz"
SHA256=$(shasum -a 256 "$TEMP_DIR/listen-$VERSION_NUM.tar.gz" | awk '{print $1}')
rm -rf "$TEMP_DIR"

info "SHA256: $SHA256"

# Update PKGBUILD
info "Updating PKGBUILD"
sed -i.bak "s/^pkgver=.*/pkgver=$VERSION_NUM/" PKGBUILD
sed -i.bak "s/^pkgrel=.*/pkgrel=1/" PKGBUILD
sed -i.bak "s/^sha256sums=.*/sha256sums=('$SHA256')/" PKGBUILD
rm PKGBUILD.bak

# Update version in listen.py
info "Updating version in listen.py"
sed -i.bak "s/^__version__ = .*/__version__ = '$VERSION_NUM'/" listen.py
rm listen.py.bak

# Update Termux build.sh
info "Updating termux/build.sh"
sed -i.bak "s/^TERMUX_PKG_VERSION=.*/TERMUX_PKG_VERSION=$VERSION_NUM/" termux/build.sh
sed -i.bak "s|^TERMUX_PKG_SRCURL=.*|TERMUX_PKG_SRCURL=https://github.com/gmoqa/listen/archive/refs/tags/v\${TERMUX_PKG_VERSION}.tar.gz|" termux/build.sh
sed -i.bak "s/^TERMUX_PKG_SHA256=.*/TERMUX_PKG_SHA256=$SHA256/" termux/build.sh
rm termux/build.sh.bak

# Generate .SRCINFO
info "Generating .SRCINFO"
if command -v makepkg &> /dev/null; then
    makepkg --printsrcinfo > .SRCINFO
else
    warn "makepkg not found, skipping .SRCINFO generation"
    warn "You'll need to run: makepkg --printsrcinfo > .SRCINFO"
fi

# Commit AUR changes
info "Committing package changes"
git add PKGBUILD .SRCINFO listen.py termux/build.sh
git commit -m "Bump version to $VERSION_NUM

$RELEASE_NOTES"

info "Pushing to main repository"
git push origin main

# Update Homebrew formula if repo exists
if [ -n "$HOMEBREW_REPO" ] && [ -d "$HOMEBREW_REPO" ]; then
    info "Updating Homebrew formula"
    cd "$HOMEBREW_REPO"

    # Update version and SHA256
    sed -i.bak "s|url \".*\"|url \"https://github.com/gmoqa/listen/archive/refs/tags/v$VERSION_NUM.tar.gz\"|" listen.rb
    sed -i.bak "s/sha256 \".*\"/sha256 \"$SHA256\"/" listen.rb
    rm listen.rb.bak

    # Commit and push
    git add listen.rb
    git commit -m "Bump version to $VERSION_NUM

$RELEASE_NOTES"
    git push origin main

    cd - > /dev/null
    info "Homebrew formula updated"
else
    warn "Skipping Homebrew update"
fi

# Sync with AUR repo if it exists
if [ -n "$AUR_REPO" ] && [ -d "$AUR_REPO" ]; then
    info "Syncing with AUR repository"

    # Copy PKGBUILD and .SRCINFO to AUR repo
    cp PKGBUILD "$AUR_REPO/PKGBUILD"

    # Generate .SRCINFO for AUR repo
    if [ -f ".SRCINFO" ]; then
        cp .SRCINFO "$AUR_REPO/.SRCINFO"
    fi

    cd "$AUR_REPO"

    # Commit and push
    git add PKGBUILD .SRCINFO
    git commit -m "Bump version to $VERSION_NUM

$RELEASE_NOTES"
    git push origin main

    cd - > /dev/null
    info "AUR repository synced"
else
    warn "Skipping AUR sync"
fi

info ""
info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
info "Release v$VERSION_NUM completed successfully!"
info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
info ""
info "Updated:"
info "  ✓ Git tag: v$VERSION_NUM"
info "  ✓ Main repo (PKGBUILD + .SRCINFO + termux/build.sh)"
if [ -n "$AUR_REPO" ] && [ -d "$AUR_REPO" ]; then
    info "  ✓ AUR repository (listen-aur)"
fi
if [ -n "$HOMEBREW_REPO" ] && [ -d "$HOMEBREW_REPO" ]; then
    info "  ✓ Homebrew formula (homebrew-listen)"
fi
info ""
info "SHA256: $SHA256"
info ""
info "Users can now install with:"
info "  brew upgrade listen              # Homebrew (macOS/Linux)"
info "  yay -Syu listen                  # AUR (Arch Linux)"
info "  pkg upgrade listen               # Termux (Android)"
info ""
