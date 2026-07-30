"""Shim — real package at src.ui. Removed in Phase 5."""
from src.ui import *  # noqa: F401,F403
from src.ui import _TEXT_CACHE  # noqa: F401 (world_scene imports this shared cache by name)
