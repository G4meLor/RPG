"""
Aetheria Gacha - Procedural Audio
Synthesizes all sound effects with numpy so the game has zero external
audio dependencies. Sounds are generated once at startup and cached.
"""
import os
import math
import numpy as np
import pygame

SOUNDS = {}
ENABLED = True
INIT_OK = False


def _make_sound(samples, sr=22050):
    """Convert a float numpy array (-1..1) to a pygame Sound."""
    samples = np.clip(samples, -1, 1)
    stereo = np.column_stack([samples, samples])
    arr = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(arr)


def _envelope(n, attack=0.05, release=0.6):
    env = np.ones(n)
    a = int(n * attack)
    r = int(n * release)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if r > 0:
        env[-r:] = np.linspace(1, 0, r)
    return env


def synth_hit(sr=22050, dur=0.18):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # low thump + noise crack
    tone = np.sin(2 * math.pi * 120 * t) * np.exp(-t * 18)
    noise = (np.random.rand(n) - 0.5) * 2 * np.exp(-t * 30)
    wave = 0.6 * tone + 0.4 * noise
    return _make_sound(wave * _envelope(n, 0.01, 0.5), sr)


def synth_crit(sr=22050, dur=0.32):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    sweep = np.sin(2 * math.pi * (200 + 1400 * t / dur) * t) * np.exp(-t * 8)
    noise = (np.random.rand(n) - 0.5) * 2 * np.exp(-t * 20)
    wave = 0.7 * sweep + 0.3 * noise
    return _make_sound(wave * _envelope(n, 0.005, 0.6), sr)


def synth_heal(sr=22050, dur=0.5):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # rising shimmering chord
    f1, f2, f3 = 523, 659, 784
    wave = (np.sin(2 * math.pi * f1 * t) + np.sin(2 * math.pi * f2 * t)
            + np.sin(2 * math.pi * f3 * t)) / 3
    wave *= np.linspace(0.3, 1, n) * np.exp(-t * 2)
    return _make_sound(wave * 0.6, sr)


def synth_buff(sr=22050, dur=0.4):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * math.pi * (300 + 600 * t / dur) * t) * np.exp(-t * 4)
    return _make_sound(wave * 0.5 * _envelope(n, 0.02, 0.6), sr)


def synth_debuff(sr=22050, dur=0.45):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * math.pi * (180 - 80 * t / dur) * t) * np.exp(-t * 3)
    noise = (np.random.rand(n) - 0.5) * 0.3 * np.exp(-t * 6)
    return _make_sound((wave + noise) * 0.6, sr)


def synth_revive(sr=22050, dur=0.8):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # bright ascending arpeggio
    wave = np.zeros(n)
    for i, f in enumerate([523, 659, 784, 1047]):
        start = int(i * n / 4)
        seg = np.sin(2 * math.pi * f * (t - t[start])) * np.exp(-(t - t[start]) * 3)
        wave += np.where(np.arange(n) >= start, seg, 0)
    return _make_sound(wave / 4 * 0.7, sr)


def synth_ultimate(sr=22050, dur=0.9):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # big cinematic boom + sweep
    sweep = np.sin(2 * math.pi * (80 + 600 * t / dur) * t) * np.exp(-t * 2)
    noise = (np.random.rand(n) - 0.5) * 2 * np.exp(-t * 5)
    wave = 0.6 * sweep + 0.4 * noise
    return _make_sound(wave * _envelope(n, 0.01, 0.5), sr)


def synth_boss_ult(sr=22050, dur=1.1):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    low = np.sin(2 * math.pi * 50 * t) * np.exp(-t * 1.5)
    sweep = np.sin(2 * math.pi * (120 - 60 * t / dur) * t)
    noise = (np.random.rand(n) - 0.5) * 2 * np.exp(-t * 3)
    wave = 0.5 * low + 0.3 * sweep + 0.3 * noise
    return _make_sound(wave * _envelope(n, 0.02, 0.5), sr)


def synth_weak(sr=22050, dur=0.25):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * math.pi * (900 - 400 * t / dur) * t) * np.exp(-t * 6)
    return _make_sound(wave * 0.5, sr)


def synth_defend(sr=22050, dur=0.2):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * math.pi * 220 * t) * np.exp(-t * 12)
    return _make_sound(wave * 0.4, sr)


def synth_gacha_roll(sr=22050, dur=1.2):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # magical shimmer
    wave = np.zeros(n)
    for f in [880, 1100, 1320]:
        wave += np.sin(2 * math.pi * f * t) * np.exp(-t * 1.5)
    wave += (np.random.rand(n) - 0.5) * 0.2 * np.exp(-t * 4)
    return _make_sound(wave / 3 * _envelope(n, 0.1, 0.4), sr)


def synth_gacha_reveal(sr=22050, dur=0.6):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * math.pi * (660 + 660 * t / dur) * t) * np.exp(-t * 3)
    return _make_sound(wave * 0.6, sr)


def synth_victory(sr=22050, dur=1.4):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # triumphant fanfare
    notes = [(523, 0.0), (659, 0.2), (784, 0.4), (1047, 0.6)]
    wave = np.zeros(n)
    for f, start in notes:
        s = int(start * sr)
        seg_t = t - t[s]
        seg = np.sin(2 * math.pi * f * seg_t) * np.exp(-seg_t * 2)
        wave += np.where(np.arange(n) >= s, seg, 0)
    return _make_sound(wave / 4 * 0.7, sr)


def synth_defeat(sr=22050, dur=1.6):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # descending sad tones
    notes = [(440, 0.0), (370, 0.3), (294, 0.6)]
    wave = np.zeros(n)
    for f, start in notes:
        s = int(start * sr)
        seg_t = t - t[s]
        seg = np.sin(2 * math.pi * f * seg_t) * np.exp(-seg_t * 1.5)
        wave += np.where(np.arange(n) >= s, seg, 0)
    return _make_sound(wave / 3 * 0.6, sr)


def synth_menu_click(sr=22050, dur=0.08):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * math.pi * 1000 * t) * np.exp(-t * 30)
    return _make_sound(wave * 0.3, sr)


def synth_hover(sr=22050, dur=0.05):
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * math.pi * 1400 * t) * np.exp(-t * 40)
    return _make_sound(wave * 0.15, sr)


def synth_skill(sr=22050, dur=0.28):
    """A bright whoosh for active skills — a quick upward sweep + airy noise."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    sweep = np.sin(2 * math.pi * (320 + 900 * t / dur) * t) * np.exp(-t * 7)
    noise = (np.random.rand(n) - 0.5) * 0.6 * np.exp(-t * 14)
    wave = 0.7 * sweep + 0.3 * noise
    return _make_sound(wave * 0.5 * _envelope(n, 0.01, 0.5), sr)


def synth_explosion(sr=22050, dur=0.5):
    """A meaty boom for bombs — low body + crackly noise tail."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    boom = np.sin(2 * math.pi * 90 * t) * np.exp(-t * 8)
    noise = (np.random.rand(n) - 0.5) * 2 * np.exp(-t * 12)
    wave = 0.6 * boom + 0.5 * noise
    return _make_sound(wave * 0.7 * _envelope(n, 0.005, 0.5), sr)


def synth_boss_intro(sr=22050, dur=1.4):
    """A heavy, ominous sting for the boss intro — a low brass swell + a hit."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # low brass: a slow swell of two close low notes
    swell = np.minimum(1.0, t / 0.4) * np.exp(-t * 1.2)
    low = (np.sin(2 * math.pi * 70 * t) + 0.6 * np.sin(2 * math.pi * 105 * t)) * swell
    # the hit at ~0.5s
    hit_t = t - 0.5
    hit = np.where(t >= 0.5,
                   np.sin(2 * math.pi * 55 * hit_t) * np.exp(-hit_t * 6), 0)
    noise = (np.random.rand(n) - 0.5) * 0.3 * np.exp(-t * 3)
    wave = 0.5 * low + 0.5 * hit + noise
    return _make_sound(wave * 0.7 * _envelope(n, 0.02, 0.4), sr)


def synth_ambience(sr=22050, dur=3.0):
    """A soft looping ambience bed — filtered noise + a low sine. Pitched by the
    caller via set_volume; meant to loop on a dedicated channel. The texture is
    deliberately quiet and low so it sits under the SFX without masking them."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # a low drone (two close low notes, slightly detuned for a beating shimmer)
    drone = (np.sin(2 * math.pi * 55 * t) + 0.7 * np.sin(2 * math.pi * 58 * t)) * 0.3
    # filtered noise: a slow, low-amplitude airy hiss (wind/room tone)
    noise = (np.random.rand(n) - 0.5)
    # crude low-pass: cumulative sum + diff smooths the noise into a soft bed
    smooth = np.cumsum(noise)
    smooth = smooth - np.linspace(smooth[0], smooth[-1], n)
    noise = smooth / (np.max(np.abs(smooth)) or 1) * 0.15
    wave = drone + noise
    # a gentle fade in/out at the loop ends so the loop point is seamless
    env = np.ones(n)
    f = int(n * 0.1)
    env[:f] = np.linspace(0, 1, f)
    env[-f:] = np.linspace(1, 0, f)
    return _make_sound(wave * env * 0.5, sr)


def synth_heartbeat(sr=22050, dur=0.6):
    """A two-pulse low thump for the low-HP heartbeat — 'lub-dub'."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.zeros(n)
    # two low thumps: one at 0.0s, one at 0.18s
    for start in (0.0, 0.18):
        st = t - start
        seg = np.where(t >= start,
                       np.sin(2 * math.pi * 60 * st) * np.exp(-st * 18), 0)
        wave += seg
    return _make_sound(wave * 0.6, sr)


def synth_perfect(sr=22050, dur=0.18):
    """A bright ping for a perfect dodge — a high sine with a quick decay."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * math.pi * 1200 * t) * np.exp(-t * 22)
    # a little shimmer harmonic so it rings clearly over combat SFX
    wave += 0.3 * np.sin(2 * math.pi * 1800 * t) * np.exp(-t * 28)
    return _make_sound(wave * 0.5, sr)


def init():
    global INIT_OK, SOUNDS, ENABLED
    if INIT_OK:
        return
    try:
        # The mixer may already be running (main.py calls pygame.init() first,
        # which starts the mixer at the default 44100 Hz). pre_init is a no-op
        # in that case, so quit + re-init at 22050 to match the synth sample rate
        # (otherwise every sound plays 2x too fast / pitched up).
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.mixer.pre_init(22050, -16, 2, 512)
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        SOUNDS = {
            "hit": synth_hit(),
            "crit": synth_crit(),
            "heal": synth_heal(),
            "buff": synth_buff(),
            "debuff": synth_debuff(),
            "revive": synth_revive(),
            "ultimate": synth_ultimate(),
            "boss_ult": synth_boss_ult(),
            "weak": synth_weak(),
            "defend": synth_defend(),
            "gacha_roll": synth_gacha_roll(),
            "gacha_reveal": synth_gacha_reveal(),
            "victory": synth_victory(),
            "defeat": synth_defeat(),
            "menu_click": synth_menu_click(),
            "hover": synth_hover(),
            "skill": synth_skill(),
            "explosion": synth_explosion(),
            "boss_intro": synth_boss_intro(),
            "ambience": synth_ambience(),
            "heartbeat": synth_heartbeat(),
            "perfect": synth_perfect(),
        }
        INIT_OK = True
    except Exception as e:
        INIT_OK = False
        ENABLED = False


# Master volume applied to every sound on play (0..1). The settings menu scales
# this; individual play() calls are multiplied by it.
MASTER_VOLUME = 0.7

# A dedicated channel for the looping biome ambience so it can be started,
# swapped, and stopped independently of one-shot SFX. Reserved on init.
_AMBIENCE_CHANNEL = None
_HEARTBEAT_T = 0.0   # time until the next heartbeat tick (low-HP warning)


def play(name, volume=0.6):
    if not ENABLED or not INIT_OK:
        return
    s = SOUNDS.get(name)
    if s:
        s.set_volume(max(0.0, min(1.0, volume * MASTER_VOLUME)))
        s.play()


def set_ambience(on, volume=0.25):
    """Start/stop the looping biome ambience on its dedicated channel."""
    global _AMBIENCE_CHANNEL
    if not INIT_OK:
        return
    # the stop path bypasses the ENABLED gate — stopping is always safe, and
    # set_enabled(False) sets ENABLED=False BEFORE calling set_ambience(False),
    # so gating the stop on ENABLED would never stop the loop (the user toggling
    # sound off would leave the ambience running).
    if not ENABLED and on:
        return
    s = SOUNDS.get("ambience")
    if not s:
        return
    if on:
        try:
            if _AMBIENCE_CHANNEL is None:
                # reserve a channel for the ambience loop
                _AMBIENCE_CHANNEL = pygame.mixer.Channel(0)
            s.set_volume(max(0.0, min(1.0, volume * MASTER_VOLUME)))
            _AMBIENCE_CHANNEL.play(s, loops=-1)
        except Exception:
            _AMBIENCE_CHANNEL = None
    else:
        try:
            if _AMBIENCE_CHANNEL is not None:
                _AMBIENCE_CHANNEL.stop()
        except Exception:
            pass


def heartbeat_tick(dt, low_hp=False, volume=0.4):
    """Drive the low-HP heartbeat: ticks every 0.8s while the active hero is
    below 30% HP. Call every frame with dt; pass low_hp=False to silence it."""
    global _HEARTBEAT_T
    if not ENABLED or not INIT_OK:
        return
    if not low_hp:
        _HEARTBEAT_T = 0.0
        return
    _HEARTBEAT_T -= dt
    if _HEARTBEAT_T <= 0:
        _HEARTBEAT_T = 0.8
        play("heartbeat", volume)


def set_enabled(on):
    global ENABLED
    ENABLED = on
    if not on:
        set_ambience(False)


def set_master_volume(v):
    """Set the master SFX volume (0..1). Applied to every future play()."""
    global MASTER_VOLUME
    MASTER_VOLUME = max(0.0, min(1.0, float(v)))
