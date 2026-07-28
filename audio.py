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


def _bandpass_noise(n, sr, low, high):
    """A crude band-passed noise bed: low-pass via cumsum, high-pass via detrend.
    Returns a normalized float array in roughly -1..1."""
    noise = np.random.rand(n) - 0.5
    # low-pass: cumulative sum smooths into a soft bed
    smooth = np.cumsum(noise)
    smooth = smooth - np.linspace(smooth[0], smooth[-1], n)
    # high-pass: subtract a slow moving average so only the band between low/high
    # survives. The amount of smoothing controls the cutoff.
    if low > 0:
        win = max(1, int(sr / low))
        if win < n:
            # simple moving average via cumulative sum
            cs = np.cumsum(np.insert(smooth, 0, 0))
            ma = (cs[win:] - cs[:-win]) / win
            ma = np.pad(ma, (0, n - len(ma)), mode='edge')
            smooth = smooth - ma
    out = smooth / (np.max(np.abs(smooth)) or 1)
    return out


def synth_ambience(sr=22050, dur=3.0, biome="plains"):
    """A soft looping ambience bed — filtered noise + a low sine, varied per
    biome so each of the 5 biomes sounds distinct. Meant to loop on a dedicated
    channel. The texture is deliberately quiet and low so it sits under the SFX
    without masking them."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # per-biome drone base freq + noise color + amplitude
    if biome == "cave":
        base, detune, noise_amp = 45, 47, 0.18
    elif biome == "castle":
        base, detune, noise_amp = 60, 62, 0.08
    elif biome == "void":
        base, detune, noise_amp = 30, 31, 0.22
    elif biome == "forest":
        base, detune, noise_amp = 72, 74, 0.16
    else:  # plains (default)
        base, detune, noise_amp = 110, 113, 0.12
    # a low drone (two close low notes, slightly detuned for a beating shimmer)
    drone = (np.sin(2 * math.pi * base * t) + 0.7 * np.sin(2 * math.pi * detune * t)) * 0.3
    # filtered noise: a slow, low-amplitude airy hiss (wind/room tone),
    # band-shaped per biome so plains is bright wind, cave is resonant room tone.
    if biome == "cave":
        noise = _bandpass_noise(n, sr, 200, 800) * noise_amp
    elif biome == "forest":
        noise = _bandpass_noise(n, sr, 600, 2000) * noise_amp
    elif biome == "void":
        noise = _bandpass_noise(n, sr, 80, 200) * noise_amp
    elif biome == "castle":
        noise = _bandpass_noise(n, sr, 300, 900) * noise_amp
    else:  # plains
        noise = _bandpass_noise(n, sr, 400, 1500) * noise_amp
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


def synth_combo_sting(tier, sr=22050):
    """An ascending stinger for a combo milestone (tier 1 at combo 5, tier 2 at
    combo 10). Tier 1 is a 2-note rise; tier 2 is a 4-note ascending arpeggio
    (reuses synth_revive's arpeggio pattern at a shorter dur so it sits on top
    of combat SFX without stepping on the hit sound)."""
    if tier <= 1:
        dur = 0.28
        n = int(sr * dur)
        t = np.linspace(0, dur, n)
        wave = np.zeros(n)
        for i, f in enumerate([523, 784]):
            start = int(i * n / 2)
            seg = np.sin(2 * math.pi * f * (t - t[start])) * np.exp(-(t - t[start]) * 5)
            wave += np.where(np.arange(n) >= start, seg, 0)
        return _make_sound(wave / 2 * 0.6, sr)
    # tier 2: 4-note ascending arpeggio (same shape as synth_revive, shorter)
    dur = 0.42
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.zeros(n)
    for i, f in enumerate([523, 659, 784, 1047]):
        start = int(i * n / 4)
        seg = np.sin(2 * math.pi * f * (t - t[start])) * np.exp(-(t - t[start]) * 4)
        wave += np.where(np.arange(n) >= start, seg, 0)
    return _make_sound(wave / 4 * 0.65, sr)


def synth_combo_max(sr=22050, dur=0.7):
    """A short triumphant chord for hitting the max combo (10) — a bright
    major triad that rings once and decays, distinct from the ascending
    stingers so the climax reads as a finisher, not another tier step."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # C major triad (523/659/784) + a high shimmer (1047) for sparkle
    wave = (np.sin(2 * math.pi * 523 * t) + np.sin(2 * math.pi * 659 * t)
            + np.sin(2 * math.pi * 784 * t) + 0.5 * np.sin(2 * math.pi * 1047 * t)) / 3.5
    wave *= np.linspace(0.4, 1, n) * np.exp(-t * 3)
    return _make_sound(wave * 0.7, sr)


def synth_rain(sr=22050, dur=3.0):
    """A looping rain bed — filtered noise shaped so it reads as rain: a
    mid-frequency hiss (the falling water) + a low rumble (the wet air).
    Band-passed noise with a slow amplitude wobble so the loop isn't a flat
    static hiss. Meant to loop on a dedicated channel under the SFX."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # mid hiss: band-passed noise in the 1-6 kHz range (the splashy part)
    hiss = _bandpass_noise(n, sr, 1000, 6000) * 0.5
    # low rumble: band-passed noise in the 80-300 Hz range (the wet air)
    rumble = _bandpass_noise(n, sr, 80, 300) * 0.3
    # slow amplitude wobble so the rain intensity varies naturally over the loop
    wobble = 0.85 + 0.15 * np.sin(2 * math.pi * 0.3 * t)
    wave = (hiss + rumble) * wobble
    # gentle fade in/out at the loop ends so the loop point is seamless
    env = np.ones(n)
    f = int(n * 0.1)
    env[:f] = np.linspace(0, 1, f)
    env[-f:] = np.linspace(1, 0, f)
    return _make_sound(wave * env * 0.55, sr)


def synth_thunder(sr=22050, dur=1.4):
    """A one-shot thunder crack — a low noise burst with a sharp attack and a
    long rumbling tail. The noise is band-passed low so it reads as thunder,
    not a hit/explosion (a deeper, longer rumble than synth_explosion)."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # low rumble: band-passed noise in the 40-200 Hz range
    rumble = _bandpass_noise(n, sr, 40, 200)
    # a sharp attack at the start (the crack) + a long decay (the rolling tail)
    attack = np.exp(-t * 6)
    tail = np.exp(-t * 1.5)
    # the crack is a brief wide-band noise burst; the tail is the low rumble
    crack = (np.random.rand(n) - 0.5) * 2 * attack
    wave = 0.7 * rumble * tail + 0.3 * crack
    return _make_sound(wave * _envelope(n, 0.005, 0.7), sr)


def synth_r_steam(sr=22050, dur=0.45):
    """Steam reaction (fire+water): a filtered noise hiss + a high chime.
    The hiss is a bright band-passed noise bed that decays quickly; the
    chime is a high sine that rings over the top so the proc reads clearly."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    hiss = _bandpass_noise(n, sr, 2000, 6000) * np.exp(-t * 6)
    chime = np.sin(2 * math.pi * 1568 * t) * np.exp(-t * 9)
    chime += 0.4 * np.sin(2 * math.pi * 2093 * t) * np.exp(-t * 12)
    wave = 0.5 * hiss + 0.5 * chime
    return _make_sound(wave * 0.6 * _envelope(n, 0.01, 0.5), sr)


def synth_r_spread(sr=22050, dur=0.5):
    """Spread reaction (fire+wind): a warm low woosh + a crackle tail.
    The woosh is a low rising sweep; the crackle is short sparse noise
    bursts layered on top so it sounds like embers scattering."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    woosh = np.sin(2 * math.pi * (180 + 220 * t / dur) * t) * np.exp(-t * 5)
    crackle = (np.random.rand(n) - 0.5) * 2 * np.exp(-t * 10)
    # sparse crackle: gate the noise so only occasional samples pass
    gate = (np.random.rand(n) < 0.08).astype(float)
    crackle *= gate
    wave = 0.6 * woosh + 0.4 * crackle
    return _make_sound(wave * 0.6 * _envelope(n, 0.02, 0.5), sr)


def synth_r_freeze(sr=22050, dur=0.4):
    """Freeze reaction (water+wind): a crystalline sine ping + a glassy
    harmonic. Reuses synth_perfect's shimmer approach (a high sine + a
    brighter harmonic) but pitched and shaped so it reads as ice, not a
    dodge — longer decay, a second glassy harmonic, a tiny noise tick at
    the start for the 'crack' of ice forming."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    ping = np.sin(2 * math.pi * 1400 * t) * np.exp(-t * 10)
    # glassy harmonics so it shimmers like cracking ice
    ping += 0.4 * np.sin(2 * math.pi * 2100 * t) * np.exp(-t * 14)
    ping += 0.2 * np.sin(2 * math.pi * 2800 * t) * np.exp(-t * 18)
    # a tiny noise tick at the very start for the 'crack'
    tick = (np.random.rand(n) - 0.5) * 2 * np.exp(-t * 60)
    wave = 0.7 * ping + 0.2 * tick
    return _make_sound(wave * 0.55 * _envelope(n, 0.005, 0.6), sr)


def synth_r_rupture(sr=22050, dur=0.55):
    """Rupture reaction (light+dark): a low dissonant two-note stab + a
    noise burst. The two close low notes beat against each other (the
    dissonance) and the noise gives it a tearing edge."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    low = np.sin(2 * math.pi * 110 * t) * np.exp(-t * 6)
    low += np.sin(2 * math.pi * 117 * t) * np.exp(-t * 6)  # ~7 Hz beat
    noise = (np.random.rand(n) - 0.5) * 2 * np.exp(-t * 14)
    wave = 0.6 * low + 0.4 * noise
    return _make_sound(wave * 0.65 * _envelope(n, 0.005, 0.5), sr)


def synth_leitmotif(element, sr=22050):
    """A short per-element musical sting played on a Genshin-style party swap
    (1/2/3/4). Five distinct motifs so each of the 5 elements reads as its own
    identity (the same identity the reaction system cares about):
      fire  = a quick brass-like rising 2-note (saw-ish sine + noise),
      water = a cool descending bell (sine + harmonic),
      wind  = an open airy chirp (upward sweep + airy noise),
      light = a bright major-3rd pluck (sine + brighter harmonics),
      dark  = a low dissonant 2-note (two close low notes that beat).
    Cached as leit_<element> in SOUNDS so the swap call site is a dict lookup,
    not a re-synth per swap. Unknown elements fall back to a neutral tone."""
    dur = 0.32
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    if element == "fire":
        # quick brass-like rising 2-note: a saw-ish sine (fundamental + 2 odd
        # harmonics for the brass edge) + a noise burst, two ascending notes.
        wave = np.zeros(n)
        for i, f in enumerate([392, 523]):  # G4 -> C5, a rising 4th
            start = int(i * n / 2)
            st = t - t[start]
            seg = (np.sin(2 * math.pi * f * st)
                   + 0.5 * np.sin(2 * math.pi * 3 * f * st)
                   + 0.3 * np.sin(2 * math.pi * 5 * f * st)) / 1.8
            seg *= np.exp(-st * 8)
            wave += np.where(np.arange(n) >= start, seg, 0)
        noise = (np.random.rand(n) - 0.5) * 2 * np.exp(-t * 18)
        wave = 0.7 * wave + 0.3 * noise
        return _make_sound(wave * _envelope(n, 0.01, 0.5) * 0.6, sr)
    if element == "water":
        # cool descending bell: a sine + a higher harmonic, two descending
        # notes with a long bell-like decay.
        wave = np.zeros(n)
        for i, f in enumerate([784, 523]):  # G5 -> C5, a descending 5th
            start = int(i * n / 2)
            st = t - t[start]
            seg = (np.sin(2 * math.pi * f * st)
                   + 0.4 * np.sin(2 * math.pi * 2 * f * st)) / 1.4
            seg *= np.exp(-st * 4)
            wave += np.where(np.arange(n) >= start, seg, 0)
        return _make_sound(wave * _envelope(n, 0.005, 0.6) * 0.55, sr)
    if element == "wind":
        # open airy chirp: a quick upward sine sweep + an airy noise bed.
        sweep = np.sin(2 * math.pi * (600 + 800 * t / dur) * t) * np.exp(-t * 9)
        airy = _bandpass_noise(n, sr, 3000, 7000) * np.exp(-t * 12) * 0.4
        wave = 0.6 * sweep + 0.4 * airy
        return _make_sound(wave * _envelope(n, 0.01, 0.55) * 0.55, sr)
    if element == "light":
        # bright major-3rd pluck: a plucked string (sine + brighter harmonics)
        # on a major-3rd interval, sharp attack + medium decay.
        l_dur = 0.30
        ln = int(sr * l_dur)
        lt = np.linspace(0, l_dur, ln)
        f = 659  # E5 — a bright major-3rd above C5
        wave = (np.sin(2 * math.pi * f * lt)
                + 0.5 * np.sin(2 * math.pi * 2 * f * lt)
                + 0.25 * np.sin(2 * math.pi * 3 * f * lt)) / 1.75
        wave *= np.exp(-lt * 7)
        # a quick pluck attack: sharp rise over the first few ms
        a = max(1, int(ln * 0.005))
        wave[:a] *= np.linspace(0, 1, a)
        return _make_sound(wave * 0.6, sr)
    if element == "dark":
        # low dissonant 2-note: two close low notes that beat against each
        # other (the dissonance) + a low noise bed.
        d_dur = 0.40
        dn = int(sr * d_dur)
        dt_ = np.linspace(0, d_dur, dn)
        low = (np.sin(2 * math.pi * 130 * dt_)
               + np.sin(2 * math.pi * 138 * dt_)) / 2  # ~8 Hz beat
        low *= np.exp(-dt_ * 5)
        noise = (np.random.rand(dn) - 0.5) * 0.6 * np.exp(-dt_ * 10)
        wave = 0.7 * low + 0.3 * noise
        return _make_sound(wave * _envelope(dn, 0.01, 0.55) * 0.6, sr)
    # fallback for an unknown element (shouldn't be reached — the 5 elements
    # are the only callers): a neutral short decaying tone.
    wave = np.sin(2 * math.pi * 440 * t) * np.exp(-t * 8)
    return _make_sound(wave * 0.5, sr)


def synth_gacha_tension(sr=22050, dur=1.6):
    """A rising tension drone for the gacha roll — a low sine sweeping up in
    frequency + a growing filtered-noise bed, crescendoing toward the reveal.
    The crescendo peaks at exactly `dur` (1.6s) to match the anim_t>1.6 gate
    so the tension resolves right as the reveal fanfare fires. Played on a
    dedicated channel (4) so it can be stopped cleanly at the reveal/skip."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    # a low sine sweeping up from 60 to 200 Hz (the rising drone) + a second
    # detuned sine for a beating shimmer so the drone isn't a flat tone.
    freq = 60 + 140 * (t / dur)
    drone = np.sin(2 * math.pi * freq * t) + 0.6 * np.sin(2 * math.pi * freq * 1.01 * t)
    # growing filtered noise: a low band-passed hiss whose amplitude rises
    # across the duration so the tension builds, not just the pitch.
    noise = _bandpass_noise(n, sr, 80, 400) * np.linspace(0, 1, n)
    # crescendo: overall amplitude grows from ~0.3 to ~1.0 across the duration
    # so the drone swells toward the reveal.
    cres = np.linspace(0.3, 1.0, n)
    # small fade-in at the very start so the loop onset doesn't pop
    f = max(1, int(n * 0.03))
    env = np.ones(n)
    env[:f] = np.linspace(0, 1, f)
    wave = (0.6 * drone + 0.4 * noise) * cres * env
    return _make_sound(wave * 0.55, sr)


def synth_gacha_fanfare(rarity, sr=22050):
    """A rarity-scaled reveal fanfare for the gacha roll:
      SSR = a full 4-note ascending arpeggio + a choir-like pad (stacked
            detuned sines) so the rarest pull reads as a big moment.
      SR  = a 2-note chord (a brighter, shorter cue than R but not the full
            SSR fanfare).
      R   = a soft single chime (a gentle decaying sine so a common pull
            doesn't over-celebrate).
    Unknown rarities fall back to the R chime (defensive; the 3 rarities are
    the only callers)."""
    if rarity == "SSR":
        dur = 1.0
        n = int(sr * dur)
        t = np.linspace(0, dur, n)
        # 4-note ascending arpeggio (C5, E5, G5, C6)
        wave = np.zeros(n)
        for i, f in enumerate([523, 659, 784, 1047]):
            start = int(i * n / 4)
            st = t - t[start]
            seg = np.sin(2 * math.pi * f * st) * np.exp(-st * 2)
            wave += np.where(np.arange(n) >= start, seg, 0)
        # choir-like pad: stacked detuned sines (a chorus effect) sustained
        # under the arpeggio so the SSR reads as a big, warm moment.
        pad_freqs = [523, 525, 527]  # C5 slightly detuned for a chorus
        pad = sum(np.sin(2 * math.pi * f * t) for f in pad_freqs) / len(pad_freqs)
        pad *= np.exp(-t * 1.5) * np.linspace(0.4, 1, n)
        wave = 0.6 * wave / 4 + 0.4 * pad
        return _make_sound(wave * 0.8, sr)
    if rarity == "SR":
        dur = 0.6
        n = int(sr * dur)
        t = np.linspace(0, dur, n)
        # 2-note chord (C5 + E5) with a medium decay
        wave = (np.sin(2 * math.pi * 523 * t) + np.sin(2 * math.pi * 659 * t)) / 2
        wave *= np.exp(-t * 3) * np.linspace(0.5, 1, n)
        return _make_sound(wave * 0.7, sr)
    # R (and unknown): a soft single chime
    dur = 0.4
    n = int(sr * dur)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * math.pi * 660 * t) * np.exp(-t * 5)
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
            # one cached ambience bed per biome so each of the 5 biomes sounds
            # distinct (plains/forest/cave/castle/void) and the active bed can be
            # swapped on map enter without re-synthesizing.
            "ambience_plains": synth_ambience(biome="plains"),
            "ambience_forest": synth_ambience(biome="forest"),
            "ambience_cave": synth_ambience(biome="cave"),
            "ambience_castle": synth_ambience(biome="castle"),
            "ambience_void": synth_ambience(biome="void"),
            # weather beds: a looping rain loop (layered on a 2nd channel when
            # the current map's weather is rain/storm) + a one-shot thunder
            # crack (fired by the per-frame storm-strike path).
            "rain": synth_rain(),
            "thunder": synth_thunder(),
            # generic alias so older callers (audio.play("ambience")) still work
            "ambience": synth_ambience(biome="plains"),
            "heartbeat": synth_heartbeat(),
            "perfect": synth_perfect(),
            # combo-climax stingers: one per milestone tier (1 at combo 5,
            # 2 at combo 10) + the max-combo chord. Cached so the pitch-tier
            # block's audio.play is a dict lookup, not a re-synth per frame.
            "combo_1": synth_combo_sting(1),
            "combo_2": synth_combo_sting(2),
            "combo_max": synth_combo_max(),
            # 4 distinct element-flavored reaction stings (Steam/Spread/Freeze/
            # Rupture) so each reaction sounds different instead of the generic
            # explosion. Routed by name at the reaction call site.
            "react_steam": synth_r_steam(),
            "react_spread": synth_r_spread(),
            "react_freeze": synth_r_freeze(),
            "react_rupture": synth_r_rupture(),
            # per-element leitmotifs for the Genshin-style party swap (1/2/3/4):
            # 5 short motifs (fire/water/wind/light/dark) so each element reads
            # as its own identity on swap. Cached so the _switch call site is a
            # dict lookup, not a re-synth per swap. Routed as "leit_"+element.
            "leit_fire": synth_leitmotif("fire"),
            "leit_water": synth_leitmotif("water"),
            "leit_wind": synth_leitmotif("wind"),
            "leit_light": synth_leitmotif("light"),
            "leit_dark": synth_leitmotif("dark"),
            # gacha roll tension + rarity-scaled reveal fanfare. The tension
            # is a 1.6s rising drone (played on a dedicated channel so it can
            # be stopped cleanly at the reveal/skip); the fanfare is one cached
            # cue per rarity (SSR arpeggio+pad, SR chord, R chime) so the
            # reveal reads as rarity-scaled, not a generic reveal reuse.
            "gacha_tension": synth_gacha_tension(),
            "gacha_fanfare_ssr": synth_gacha_fanfare("SSR"),
            "gacha_fanfare_sr": synth_gacha_fanfare("SR"),
            "gacha_fanfare_r": synth_gacha_fanfare("R"),
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
# The last requested ambience volume (pre-master-scaling), remembered so
# set_master_volume can re-scale the already-playing loop when the slider moves.
_AMBIENCE_VOLUME = 0.25
# The biome currently playing on the ambience channel (set when a bed starts),
# so re-entry into the same biome updates volume without restarting the loop.
_AMBIENCE_BIOME = None
# The weather currently layered on the ambience channel ("rain" or None). When
# rain/storm, the rain bed plays on a 2nd reserved channel so the wet loop
# layers on top of the biome drone (a 2-channel bed, not a swap).
_AMBIENCE_WEATHER = None
# A dedicated channel for the layered rain loop so it can be started, swapped,
# and stopped independently of the biome ambience. Reserved on first use.
_RAIN_CHANNEL = None
_RAIN_VOLUME = 0.30
# A dedicated channel for the gacha roll tension drone so it can be started at
# the roll and stopped cleanly at the reveal (or the skip branch) without
# leaking past the reveal fanfare. Reserved on first use.
_GACHA_CHANNEL = None
# The biomes we have cached ambience beds for (matches the SOUNDS keys).
_AMBIENCE_BIOMES = ("plains", "forest", "cave", "castle", "void")
_HEARTBEAT_T = 0.0   # time until the next heartbeat tick (low-HP warning)


def play(name, volume=0.6):
    if not ENABLED or not INIT_OK:
        return
    s = SOUNDS.get(name)
    if s:
        s.set_volume(max(0.0, min(1.0, volume * MASTER_VOLUME)))
        s.play()


def set_ambience(on, volume=0.25, biome=None, weather=None):
    """Start/stop the looping biome ambience on its dedicated channel. When
    starting, the biome selects which cached bed plays so each of the 5 biomes
    sounds distinct. Re-entry with the same biome only updates the live volume
    (it does not restart the loop), so map transitions don't cause a pop/tick.

    When `weather` is "rain" (rain or storm), the rain bed is layered on a 2nd
    reserved channel so the world sounds wet — a filtered-noise loop on top of
    the biome drone (a 2-channel bed, not a swap). Clear weather stops the rain
    bed so leaving a storm map silences the wet loop."""
    global _AMBIENCE_CHANNEL, _AMBIENCE_VOLUME, _AMBIENCE_BIOME, _AMBIENCE_WEATHER
    if not INIT_OK:
        return
    # the stop path bypasses the ENABLED gate — stopping is always safe, and
    # set_enabled(False) sets ENABLED=False BEFORE calling set_ambience(False),
    # so gating the stop on ENABLED would never stop the loop (the user toggling
    # sound off would leave the ambience running).
    if not on:
        try:
            if _AMBIENCE_CHANNEL is not None:
                _AMBIENCE_CHANNEL.stop()
                _AMBIENCE_CHANNEL._ambience_key = None
        except Exception:
            pass
        _stop_rain_bed()
        _AMBIENCE_BIOME = None
        _AMBIENCE_WEATHER = None
        return
    if not ENABLED:
        return
    # pick the cached bed for this biome (fall back to plains if unknown)
    key = "ambience_" + (biome if biome in _AMBIENCE_BIOMES else "plains")
    s = SOUNDS.get(key)
    if not s:
        return
    _AMBIENCE_VOLUME = max(0.0, min(1.0, float(volume)))
    _AMBIENCE_BIOME = biome if biome in _AMBIENCE_BIOMES else "plains"
    _AMBIENCE_WEATHER = weather
    try:
        if _AMBIENCE_CHANNEL is None:
            # reserve a channel for the ambience loop
            _AMBIENCE_CHANNEL = pygame.mixer.Channel(0)
        s.set_volume(max(0.0, min(1.0, _AMBIENCE_VOLUME * MASTER_VOLUME)))
        # only (re)start the loop if the channel is idle OR a different biome bed
        # is currently playing — re-entry into the same biome just updates volume.
        current = getattr(_AMBIENCE_CHANNEL, "_ambience_key", None)
        if not _AMBIENCE_CHANNEL.get_busy() or current != key:
            _AMBIENCE_CHANNEL.play(s, loops=-1)
            _AMBIENCE_CHANNEL._ambience_key = key
    except Exception:
        _AMBIENCE_CHANNEL = None
    # rain bed: layer a filtered-noise loop on a 2nd channel when the weather is
    # rain/storm; stop it when the weather is clear/fog so the wet loop only
    # plays on wet maps (not silent-then-pop on the next dry map).
    if weather == "rain":
        _start_rain_bed(volume=0.30)
    else:
        _stop_rain_bed()


def _start_rain_bed(volume=0.30):
    """Layer the cached rain loop on a 2nd reserved channel so it sits on top of
    the biome ambience. Re-entry while the rain bed is already playing only
    updates the live volume (no restart, no pop)."""
    global _RAIN_CHANNEL, _RAIN_VOLUME
    if not INIT_OK or not ENABLED:
        return
    s = SOUNDS.get("rain")
    if s is None:
        return
    _RAIN_VOLUME = max(0.0, min(1.0, float(volume)))
    try:
        if _RAIN_CHANNEL is None:
            _RAIN_CHANNEL = pygame.mixer.Channel(1)
        s.set_volume(max(0.0, min(1.0, _RAIN_VOLUME * MASTER_VOLUME)))
        current = getattr(_RAIN_CHANNEL, "_rain_key", None)
        if not _RAIN_CHANNEL.get_busy() or current != "rain":
            _RAIN_CHANNEL.play(s, loops=-1)
            _RAIN_CHANNEL._rain_key = "rain"
    except Exception:
        _RAIN_CHANNEL = None


def _stop_rain_bed():
    """Stop the layered rain loop (called on a transition to clear/fog weather
    or when the ambience is stopped entirely)."""
    global _RAIN_CHANNEL
    try:
        if _RAIN_CHANNEL is not None:
            _RAIN_CHANNEL.stop()
            _RAIN_CHANNEL._rain_key = None
    except Exception:
        pass


def play_thunder(volume=0.6):
    """Play a one-shot thunder crack on top of the ambience (called by the
    world scene's per-frame storm-strike path). A distinct low noise burst so
    it reads as thunder, not a hit."""
    play("thunder", volume)


def heartbeat_tick(dt, low_hp=False, volume=0.4, hp_frac=1.0):
    """Drive the low-HP heartbeat: ticks faster and louder as the active hero
    gets closer to death. Call every frame with dt; pass low_hp=False to
    silence it. hp_frac (0..1) scales the interval and volume for tension."""
    global _HEARTBEAT_T
    if not ENABLED or not INIT_OK:
        return
    if not low_hp:
        _HEARTBEAT_T = 0.0
        return
    # faster (0.5s) and louder as HP drops below 20%; 0.8s/0.4 vol above that.
    frac = max(0.0, min(1.0, float(hp_frac)))
    interval = 0.5 if frac <= 0.2 else 0.8
    # volume grows from the base 0.4 up to ~0.7 as HP approaches 0 within the
    # low-HP band (0..0.3): at 0.3 it's 0.4, at 0.0 it's ~0.7.
    vol = volume + max(0.0, (1.0 - frac / 0.3)) * 0.3
    _HEARTBEAT_T -= dt
    if _HEARTBEAT_T <= 0:
        _HEARTBEAT_T = interval
        play("heartbeat", vol)


def set_enabled(on):
    global ENABLED
    ENABLED = on
    if not on:
        set_ambience(False)
        _stop_rain_bed()
        stop_gacha_tension()


def set_master_volume(v):
    """Set the master SFX volume (0..1). Applied to every future play(), and
    re-applied to the already-playing ambience loop so the slider affects the
    live bed instead of only future one-shots."""
    global MASTER_VOLUME
    MASTER_VOLUME = max(0.0, min(1.0, float(v)))
    if _AMBIENCE_CHANNEL is not None and _AMBIENCE_CHANNEL.get_busy():
        s = SOUNDS.get("ambience_" + (_AMBIENCE_BIOME or "plains"))
        if s:
            s.set_volume(max(0.0, min(1.0, _AMBIENCE_VOLUME * MASTER_VOLUME)))


def play_gacha_tension(volume=0.5):
    """Start the 1.6s gacha roll tension drone on its dedicated channel. The
    channel is reserved on first use and stopped at the reveal/skip via
    stop_gacha_tension() so the drone never leaks past the reveal fanfare."""
    global _GACHA_CHANNEL
    if not INIT_OK:
        return
    s = SOUNDS.get("gacha_tension")
    if s is None:
        return
    vol = max(0.0, min(1.0, float(volume) * MASTER_VOLUME)) if ENABLED else 0.0
    s.set_volume(vol)
    try:
        if _GACHA_CHANNEL is None:
            _GACHA_CHANNEL = pygame.mixer.Channel(4)
        _GACHA_CHANNEL.play(s)
    except Exception:
        _GACHA_CHANNEL = None


def stop_gacha_tension():
    """Stop the gacha tension drone (called at the reveal or the skip branch).
    The stop path bypasses the ENABLED gate — stopping is always safe, and a
    user toggling sound off mid-roll must still silence the drone."""
    global _GACHA_CHANNEL
    try:
        if _GACHA_CHANNEL is not None:
            _GACHA_CHANNEL.stop()
    except Exception:
        pass
