#!/usr/bin/env bash
set -euo pipefail

echo
echo "This helper prints the pacman commands needed on Arch Linux to prepare the system for Playwright + building greenlet."
echo "It does NOT run anything by default. Pass --run to execute with sudo."
echo

PACMAN_PKGS=(
  base-devel
  python
  python-pip
  python-wheel
  python-setuptools
  python-virtualenv
  gcc
  libx11
  libxkbcommon
  libxcomposite
  libxrandr
  libxrender
  libxss
  alsa-lib
  libgdk-pixbuf2
  gtk3
  nss
  cups
  dbus
  libdrm
  libxdamage
  libgbm
)

echo "Required pacman packages (recommended):"
for p in "${PACMAN_PKGS[@]}"; do
  echo "  - $p"
done

echo
CMD="sudo pacman -S --needed --noconfirm ${PACMAN_PKGS[*]}"
echo "Run this command to install system deps:"
echo
echo "  $CMD"

if [ "${1:-}" = "--run" ]; then
  echo
  echo "Running: $CMD"
  eval "$CMD"
fi

echo
echo "After installing system packages, create/activate your venv and install Python deps:" 
echo
echo "  python -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install --upgrade pip"
echo "  pip install -r requirements.txt"
echo "  # Install Playwright browsers"
echo "  playwright install --with-deps"
echo
echo "If you still encounter greenlet build errors, consider switching to Python 3.11 where binary wheels are widely available:"
echo "  sudo pacman -S python3.11"

exit 0
