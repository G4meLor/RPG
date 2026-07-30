"""Shim — real module at src.audio. Removed in Phase 5.

Proxies attribute access to src.audio via PEP 562 __getattr__ instead of
star-import, because src.audio rebinds module globals at runtime (SOUNDS,
INIT_OK, ENABLED are reassigned inside init()/set_enabled()/set_master_volume).
A star-import would copy the *initial* values (SOUNDS={}) at import time and
never see the rebound dict, so `audio.SOUNDS` after `audio.init()` would stay
empty. __getattr__ reads the live attribute on every access.
"""
import src.audio as _real


def __getattr__(name):
    return getattr(_real, name)


def __setattr__(name, value):
    setattr(_real, name, value)


def __dir__():
    return dir(_real)
