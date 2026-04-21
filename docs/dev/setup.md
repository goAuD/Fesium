# Development Setup

## Requirements

- Python 3.8 or newer
- PHP on your system `PATH` if you want to test the PHP-backed local server flow (optional; Fesium falls back to a static server when PHP is unavailable)

Check PHP availability:

```bash
php -v
```

## Install

```bash
git clone https://github.com/goAuD/Fesium.git
cd Fesium
python -m pip install -r requirements.txt
```

`requirements.txt` is the single source for both runtime and contributor dependencies (pytest included).

## Run the App

Primary launcher:

```bash
python fesium.py
```

Legacy compatibility launcher (will be removed in a future release):

```bash
python nanoserver.py
```

The two launchers are functionally equivalent today. Prefer `fesium.py` in new documentation and scripts.

## Next Steps

- [testing.md](testing.md) — how to run the test suite
- [conventions.md](conventions.md) — repo structure, code organization, and design/security rules
