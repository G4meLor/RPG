"""Thin entry shim invoked by the root main.py. The real Game lives in
src.core.game; this just wires sys.path + pygame + runs the loop so the
root main.py stays a one-liner."""
import os
import sys

# ensure the repo root (parent of src/) is on sys.path so `import src...` works
# when launched as `python3 main.py`
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pygame
from src.core.game import Game  # noqa: E402


def main():
    pygame.init()
    Game().run()


if __name__ == "__main__":
    main()
