"""Aetheria — open-world 2D gacha RPG (170 LoL champions). Thin entry point.

The game lives in the src/ package; this just bootstraps it. Run: python3 main.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.main import main  # noqa: E402
from src.core.game import Game  # noqa: E402  (re-exported so `main.Game` resolves)

if __name__ == "__main__":
    main()
