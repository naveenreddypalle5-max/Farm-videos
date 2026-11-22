#!/usr/bin/env python3
"""Compose and synthesise a soft Indian instrumental for the reel.

Raag Bhupali (Sa Re Ga Pa Dha) in D, 80 BPM. Tanpura drone, bansuri-style
flute, santoor-style plucks, a gentle frame drum and a pad, with hall reverb.
Every sound is synthesised here, so there is no third-party audio and no
copyright issue.

Usage: python3 make_music.py <out.wav> [total_seconds]
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
BPM = 80.0
BEAT = 60.0 / BPM
OUT = sys.argv[1]
TOTAL = float(sys.argv[2]) if len(sys.argv) > 2 else 34.5
N = int((TOTAL + 0.2) * SR)
rng = np.random.default_rng(7)

# Bhupali swaras in D
SA = 146.83  # D3
RATIO = {"S": 1.0, "R": 9 / 8, "G": 5 / 4, "P": 3 / 2, "D": 5 / 3}


def hz(sw, octv=1):
    """'S' ... 'D' with octave: 0 = D2 range, 1 = D3, 2 = D4 (flute mid), 3 = D5."""
    return SA * RATIO[sw] * (2 ** (octv - 1))


def b2s(beat):
    return int(round(beat * BEAT * SR))


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def add(buf, start, sig):
    if start >= len(buf):
        return
    end = min(len(buf), start + len(sig))
    buf[start:end] += sig[: end - start]


def automation(points, n=N):
    """Piecewise-linear gain curve from [(seconds, gain), ...]."""
    t = np.arange(n) / SR
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)


# ---------------------------------------------------------------- tanpura
def tanpura_pluck(f, dur=6.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 28):
        fk = f * k * (1 + 0.0004 * rng.standard_normal())
        if fk > 9000:
            break
        # jawari: energy sweeps up through the harmonics after the pluck
        peak = 0.25 + 0.06 * k
        env = (t / peak) * np.exp(1 - t / peak) if k > 2 else np.exp(-t / 3.5)
        env *= np.exp(-t / (5.5 / (1 + 0.04 * k)))
        amp = 1.0 / (k ** 0.9)
        out += amp * env * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6.28))
    out *= np.minimum(1, t / 0.004)
    return out / 6.0


tanpura = np.zeros(N)
cycle = [hz("P", 0) * 1, hz("S", 1), hz("S", 1), hz("S", 0)]  # Pa Sa Sa Sa
step = 0.75  # seconds between strings: one cycle per 3 s (one bar)
t0 = 0.0
i = 0
while t0 < TOTAL:
    add(tanpura, int(t0 * SR), tanpura_pluck(cycle[i % 4]) * (1.15 if i % 4 == 3 else 1.0))
    t0 += step + rng.uniform(-0.02, 0.02)
    i += 1
tanpura = lp(tanpura, 5000)


# ---------------------------------------------------------------- flute
def flute_phrase(notes):
    """notes: list of (start_beat, dur_beats, swara, octave). Played legato."""
    s0 = b2s(notes[0][0])
    s1 = b2s(notes[-1][0] + notes[-1][1])
    n = s1 - s0 + int(0.5 * SR)
    t = np.arange(n) / SR
    f = np.zeros(n)
    amp = np.zeros(n)
    prev = None
    for (sb, db, sw, o) in notes:
        a = b2s(sb) - s0
        b = b2s(sb + db) - s0
        target = hz(sw, o)
        seg_t = np.arange(b - a) / SR
        if prev is None:
            f[a:b] = target
        else:  # meend: glide into the note
            g = 1 - np.exp(-seg_t / 0.045)
            f[a:b] = prev * (target / prev) ** g
        # vibrato that blooms on longer notes
        depth = np.clip((seg_t - 0.25) / 0.5, 0, 1) * 0.006 * min(1.0, db)
        f[a:b] *= 1 + depth * np.sin(2 * np.pi * 5.1 * seg_t)
        # gentle re-articulation at each note start
        art = 1 - 0.28 * np.exp(-seg_t / 0.05) if prev is not None else np.ones(b - a)
        amp[a:b] = art * (0.85 + 0.15 * np.clip(seg_t / 0.4, 0, 1))
        prev = target
    end = b2s(notes[-1][0] + notes[-1][1]) - s0
    f[end:] = prev
    # phrase envelope: soft attack, natural release
    env = np.minimum(1, t / 0.12)
    rel = np.clip(1 - (t - end / SR) / 0.35, 0, 1)
    env *= np.where(t > end / SR, rel, 1)
    amp *= env
    amp[end:] = env[end:]
    amp *= 1 + 0.03 * lp(rng.standard_normal(n), 6)  # breath flutter
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = (np.sin(ph) + 0.22 * np.sin(2 * ph + 0.3) + 0.09 * np.sin(3 * ph + 1.1)
            + 0.035 * np.sin(4 * ph))
    breath = bp(rng.standard_normal(n), 900, 5200) * 0.11
    sig = (tone + breath * (0.6 + 0.4 * np.exp(-t / 0.15))) * amp
    return s0, lp(sig, 6500)


# Melody (start beat, length in beats, swara, octave). Octave 2 = D4 region.
PHRASES = [
    # opening alaap: milk
    [(0.5, 1.0, "P", 1), (1.5, 2.5, "S", 2), (4.0, 0.5, "R", 2), (4.5, 2.5, "G", 2)],
    [(7.5, 0.5, "G", 2), (8.0, 1.25, "P", 2), (9.25, 0.75, "D", 2), (10.0, 1.0, "P", 2),
     (11.0, 1.5, "G", 2), (12.5, 0.5, "R", 2), (13.0, 2.0, "S", 2)],
    # churning: a rhythmic, rising line
    [(16.0, 0.5, "S", 2), (16.5, 0.5, "R", 2), (17.0, 1.0, "G", 2), (18.0, 1.0, "P", 2),
     (19.0, 0.5, "G", 2), (19.5, 0.5, "P", 2), (20.0, 2.0, "D", 2), (22.0, 1.0, "P", 2),
     (23.0, 1.0, "G", 2), (24.0, 2.0, "R", 2)],
    # golden ghee: climax in the upper register
    [(26.5, 0.5, "P", 2), (27.0, 2.0, "S", 3), (29.0, 0.5, "D", 2), (29.5, 0.5, "S", 3),
     (30.0, 1.5, "R", 3), (31.5, 0.5, "S", 3), (32.0, 1.0, "D", 2), (33.0, 1.0, "P", 2),
     (34.0, 1.0, "G", 2), (35.0, 0.5, "P", 2), (35.5, 0.5, "D", 2), (36.0, 1.0, "P", 2),
     (37.0, 1.0, "G", 2), (38.0, 1.0, "R", 2)],
    # end card: resolve home to Sa
    [(39.0, 5.5, "S", 2)],
]
flute = np.zeros(N)
for ph in PHRASES:
    s0, sig = flute_phrase(ph)
    add(flute, s0, sig)


# ---------------------------------------------------------------- santoor
def santoor(f, vel=1.0, dur=2.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 9):
        fk = f * k * (1 + 0.0008 * k * k)
        if fk > 12000:
            break
        for det in (-0.6, 0.6):  # paired strings, slight chorus
            out += (1 / k) * np.exp(-t * (1.6 + 0.9 * k)) * np.sin(2 * np.pi * (fk + det) * t)
    out *= np.minimum(1, t / 0.002)
    return out * vel * 0.18


ARP = {
    "a": [("S", 2), ("P", 2), ("S", 3), ("P", 2), ("G", 2), ("P", 2), ("S", 3), ("P", 2)],
    "b": [("S", 2), ("G", 2), ("P", 2), ("D", 2), ("S", 3), ("D", 2), ("P", 2), ("G", 2)],
    "c": [("P", 2), ("S", 3), ("R", 3), ("S", 3), ("D", 2), ("S", 3), ("G", 3), ("R", 3)],
}
plucks = np.zeros(N)
bar_patterns = {2: "a", 3: "a", 4: "b", 5: "a", 6: "b", 7: "b", 8: "c", 9: "c"}
for bar, pat in bar_patterns.items():
    for j, (sw, o) in enumerate(ARP[pat]):
        beat = bar * 4 + j * 0.5
        if beat < 6:
            continue
        vel = (0.9 if j % 2 == 0 else 0.6) * (1.15 if bar >= 8 else 1.0)
        add(plucks, b2s(beat) + int(rng.uniform(0, 0.006) * SR), santoor(hz(sw, o), vel))
# end card: slow descending cascade then home
for j, (sw, o) in enumerate([("S", 3), ("D", 2), ("P", 2), ("G", 2), ("R", 2), ("S", 2)]):
    add(plucks, b2s(39.0 + j * 0.5), santoor(hz(sw, o), 0.8 - j * 0.05, dur=3.5))
add(plucks, b2s(42.5), santoor(hz("S", 1), 0.7, dur=3.5))


# ---------------------------------------------------------------- frame drum
def dhum(vel=1.0):
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    f = 58 + 70 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28)
    thump = lp(rng.standard_normal(n), 900) * np.exp(-t / 0.012) * 0.4
    return (body + thump) * vel * 0.55


def ta(vel=1.0):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    ring = np.sin(2 * np.pi * 420 * t) * np.exp(-t / 0.07) * 0.5
    snap = bp(rng.standard_normal(n), 1500, 6000) * np.exp(-t / 0.015)
    return (ring + snap) * vel * 0.22


drum = np.zeros(N)
for beat in np.arange(12.0, 39.0, 1.0):
    pos = beat % 4
    if pos in (0.0,):
        add(drum, b2s(beat), dhum(1.0))
    if pos == 2.5:
        add(drum, b2s(beat), dhum(0.6))
    if pos in (1.0, 3.0):
        add(drum, b2s(beat), ta(0.7))
    if pos == 2.0:
        add(drum, b2s(beat), ta(0.45))
    if pos == 3.0 and beat > 26:
        add(drum, b2s(beat + 0.5), ta(0.35))
for fb, v in [(25.0, 0.5), (25.5, 0.6), (25.75, 0.7), (26.0, 0.85)]:  # fill into the climax
    add(drum, b2s(fb), ta(v))
add(drum, b2s(27.0), dhum(1.1))
add(drum, b2s(39.0), dhum(1.3))  # landing on the end card

# ---------------------------------------------------------------- pad + swell
t = np.arange(N) / SR
pad = np.zeros(N)
for f, a in [(hz("S", 1), 1.0), (hz("P", 1), 0.7), (hz("S", 2), 0.5), (hz("G", 2), 0.22)]:
    for det in (-0.25, 0.0, 0.25):
        ph = 2 * np.pi * (f * (1 + det / 100)) * t + rng.uniform(0, 6.28)
        pad += a * (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph))
pad = lp(pad, 1400) * 0.05
pad *= automation([(0, 0), (6, 0.25), (19, 0.55), (27, 1.0), (31, 0.85), (33, 1.0), (TOTAL, 0.6)])

swell = bp(rng.standard_normal(N), 700, 7000) * 0.06
swell *= automation([(0, 0), (b2s(36.5) / SR, 0), (b2s(39.0) / SR - 0.05, 1), (b2s(39.0) / SR, 0), (TOTAL, 0)]) ** 2

# ---------------------------------------------------------------- mix
def pan(x, p):  # p: -1 left .. 1 right
    return np.stack([x * np.sqrt((1 - p) / 2), x * np.sqrt((1 + p) / 2)])


mix = (pan(tanpura * 0.55, -0.25)
       + pan(flute * 0.42, 0.08)
       + pan(plucks * 0.75, 0.3)
       + pan(drum * 0.85, -0.05)
       + pan(pad, 0.0)
       + pan(swell, 0.0))
mix[:, :] = np.stack([hp(mix[0], 35), hp(mix[1], 35)])


# hall reverb (decorrelated exponential noise tails)
def ir(seed, sec=2.8):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    tt = np.arange(n) / SR
    x = r.standard_normal(n) * np.exp(-tt / 0.75)
    x = lp(x, 6000) * np.minimum(1, tt / 0.012)
    return x / np.sqrt(np.sum(x ** 2))


wet = np.stack([fftconvolve(mix[0], ir(1))[:N], fftconvolve(mix[1], ir(2))[:N]])
out = mix * 0.8 + wet * 0.55

# master fades + gentle soft-clip
fade = automation([(0, 0), (1.2, 1), (TOTAL - 1.8, 1), (TOTAL, 0)])
out *= fade
out /= np.max(np.abs(out)) + 1e-9
out = np.tanh(out * 1.2) / np.tanh(1.2)
out *= 0.89
wavfile.write(OUT, SR, (out.T * 32767).astype(np.int16))
print(f"wrote {OUT}: {N / SR:.2f}s @ {BPM:.0f} BPM")
