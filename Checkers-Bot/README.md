# Checkers Bot

Simple checkers implementations and a Human vs AI playable game.

## Overview
- `final.py`: An "early game" implementation — a work-in-progress with polished piece/board visuals, windowed 800×800 UI, and an AI using minimax. Uses `numpy` and `pygame`.
- `human-vs-AI-play.py`: The official, polished, and hardest playable game. Fullscreen, crisp UI, marble textures, a side panel, and the Human vs AI experience. Uses `pygame`.

## Requirements
- Python 3.8 or newer
- `pygame` (required)
- `numpy` (required only for `final.py`)

Install with:

```bash
python -m pip install --upgrade pip
python -m pip install pygame numpy
```

If you only plan to run `human-vs-AI-play.py`, installing `pygame` is sufficient:

```bash
python -m pip install pygame
```

## Running
- Run the official game (recommended / hardest):

```bash
python human-vs-AI-play.py
```

- Run the early-game demo:

```bash
python final.py
```

Notes:
- `human-vs-AI-play.py` starts in fullscreen and detects your display resolution. Press `Esc` to exit.
- Controls are click-to-select a piece, then click a move dot to move.
- Both games use a minimax-based AI (depth=3 by default).

## Files
- [human-vs-AI-play.py](human-vs-AI-play.py) — Official game (recommended)
- [final.py](final.py) — Early-game prototype
- `Checkers Bot/` — Additional project assets and modules (if present)

## License
Add a license if you want to share this project publicly.

---

If you'd like, I can also create a `requirements.txt`, add a small README badge, or update the repo description.