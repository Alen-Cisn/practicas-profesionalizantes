
# Arch Linux: setup for Playwright + greenlet (E2E tests)

This document collects the exact steps to prepare an Arch Linux host so you can run the Playwright E2E tests included in this repository.


Summary: install system packages, create a Python venv, install Python deps, install Playwright browsers.

## Install system dependencies (recommended)

Run the following (copy/paste):

```bash
sudo pacman -Syu
sudo pacman -S --needed base-devel python python-pip python-wheel python-setuptools python-virtualenv \
  gcc libx11 libxkbcommon libxcomposite libxrandr libxrender libxss alsa-lib libgdk-pixbuf2 gtk3 nss cups dbus libdrm libxdamage libgbm
```

These packages provide the build toolchain and the runtime libraries that Playwright needs and that allow building C extensions like `greenlet`.


## Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

## Install Python dependencies

From the repository root:

```bash
pip install -r requirements.txt
# If the project pins playwright but greenlet fails to build, try to install playwright without forcing a specific greenlet source:
# pip install --prefer-binary playwright
```


## Install Playwright browsers and system dependencies for browsers

```bash
# inside the venv
playwright install --with-deps
```

On Arch, Playwright will attempt to install the browser binaries. If some browser system dependencies are missing, install them using pacman (see step 1).

## Troubleshooting greenlet build failures

If you see errors similar to "error: this header requires Py_BUILD_CORE define" or lots of C++ compile failures, it's usually because the installed Python headers don't match the binary or the build environment is missing.

Solutions:

1. Ensure you installed `python` and `base-devel` as above.
2. Use a widely-supported Python version (3.11 or 3.12) where prebuilt greenlet wheels are available. For example, install `python3.11` from pacman and create the venv with that interpreter: `python3.11 -m venv venv`.
3. If you need to keep Python 3.13, you may need to install additional dev headers or use system packages built for 3.13 — these can be brittle.

## Running the E2E tests

1. Start Streamlit (use MOCK_CDX to avoid external web.archive.org dependency):

```bash
export MOCK_CDX=true
./launch_app.sh &
```

## Run tests with pytest

```bash
pytest tests/e2e -q
```

## CI recommendation

For CI (GitHub Actions), use `ubuntu-latest`. Ubuntu runners usually have compatible tooling and Playwright supports installing system deps (`playwright install --with-deps`) there. If you prefer, I can add a GitHub Actions workflow that runs the E2E tests under MOCK_CDX=true.

If you want me to add the workflow file now, say so and I'll create it.
