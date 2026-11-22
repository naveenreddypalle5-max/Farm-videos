#!/usr/bin/env python3
"""Music for reel 3: sitar-style lead with tabla (keherwa), Raag Yaman, 88 BPM.

Tanpura drone, sitar-like plucked lead with meend, tabla, a soft pad and
hall reverb. Fully synthesised here, so it is free of copyright.

Usage: python3 make_music_3.py <out.wav> [total_seconds]
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
BPM = 88.0
BEAT = 60.0 / BPM
OUT = sys.argv[1]
TOTAL = float(sys.argv[2]) if len(sys.argv) > 2 else 33.4
N = int((TOTAL + 0.2) * SR)
rng = np.random.default_rng(23)

SA = 138.59  # C#3
RATIO = {"S": 1, "R": 9 / 8, "G": 5 / 4, "m": 45 / 32, "P": 3 / 2, "D": 5 / 3, "N": 15 / 8}
GROOVE_IN, END = 8, 41  # tabla from beat 8; end card from beat 41


def hz(sw, o=1):
    return SA * RATIO[sw] * 2 ** (o - 1)


def b2s(b):
    return int(round(b * BEAT * SR))


def filt(x, kind, fc, order=2):
    return sosfilt(butter(order, fc, kind, fs=SR, output="sos"), x)


def add(buf, start, sig):
    if 0 <= start < len(buf):
        e = min(len(buf), start + len(sig))
        buf[start:e] += sig[: e - start]


def curve(points):
    xs, ys = zip(*points)
    return np.interp(np.arange(N) / SR, xs, ys)


def sitar(f, dur, vel=1.0, glide_from=None):
    """Bright plucked string with a jawari-style buzz sweeping up the partials."""
    n = int((dur + 1.2) * SR)
    t = np.arange(n) / SR
    fcurve = np.full(n, f)
    if glide_from:  # meend: pull the string from a neighbouring note
        g = 1 - np.exp(-t / 0.09)
        fcurve = glide_from * (f / glide_from) ** g
    ph = 2 * np.pi * np.cumsum(fcurve) / SR
    out = np.zeros(n)
    for k in range(1, 24):
        if f * k > 10000:
            break
        peak = 0.02 + 0.012 * k
        env = np.minimum(1, t / peak) * np.exp(-t / (1.1 / (1 + 0.06 * k)))
        out += (1 / k ** 0.75) * env * np.sin(k * ph + rng.uniform(0, 6.28))
    out *= np.minimum(1, t / 0.002)
    rel = np.clip(1 - (t - dur) / 0.6, 0, 1)
    return filt(out * rel, "low", 7000) * vel * 0.12


def tanpura(f):
    n = int(5.5 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 22):
        peak = 0.25 + 0.06 * k
        env = (t / peak) * np.exp(1 - t / peak) * np.exp(-t / (5 / (1 + 0.04 * k)))
        out += env * np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6.28)) / k ** 0.9
    return out * np.minimum(1, t / 0.004) / 7


def bayan(vel=1.0, glide=False):  # tabla bass drum
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    f = 70 + 40 * np.exp(-t / 0.03) + (25 * (1 - np.exp(-t / 0.12)) if glide else 0)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.3) * vel * 0.55


def dayan(vel=1.0, open_=True):  # tabla treble drum: harmonic ring or muted tap
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    f0 = 2 * SA * 2  # tuned to Sa
    dec = 0.18 if open_ else 0.03
    ring = sum(a * np.sin(2 * np.pi * f0 * m * t) for m, a in [(1, 1), (2, 0.6), (3, 0.45), (4, 0.3), (5, 0.2)])
    hit = filt(rng.standard_normal(n), "band", [2000, 8000]) * np.exp(-t / 0.008)
    return (ring * np.exp(-t / dec) * 0.35 + hit * 0.6) * vel * 0.3


# ---------------------------------------------------------------- tanpura
drone = np.zeros(N)
tt, i = 0.0, 0
for_cycle = [hz("P", 0), hz("S", 1), hz("S", 1), hz("S", 0)]
while tt < TOTAL:
    add(drone, int(tt * SR), tanpura(for_cycle[i % 4]))
    tt += BEAT * 1.0
    i += 1

# ---------------------------------------------------------------- sitar melody (Yaman)
# (beat, length, swara, octave, glide-from swara or None)
MEL = [
    (0.0, 2.0, "N", 1, None), (2.0, 2.0, "R", 2, "S"), (4.0, 1.0, "G", 2, None),
    (5.0, 1.0, "m", 2, None), (6.0, 2.0, "G", 2, "m"),
    # groove enters
    (8.0, 0.5, "N", 1, None), (8.5, 0.5, "R", 2, None), (9.0, 1.0, "G", 2, None), (10.0, 0.5, "m", 2, None),
    (10.5, 0.5, "D", 2, None), (11.0, 1.0, "P", 2, "D"), (12.0, 1.0, "m", 2, None), (13.0, 1.0, "G", 2, None),
    (14.0, 2.0, "R", 2, "G"),
    (16.0, 0.5, "P", 2, None), (16.5, 0.5, "m", 2, None), (17.0, 0.5, "D", 2, None), (17.5, 0.5, "N", 2, None),
    (18.0, 1.0, "S", 3, "N"), (19.0, 1.0, "N", 2, None), (20.0, 1.0, "D", 2, None), (21.0, 1.0, "P", 2, None),
    (22.0, 2.0, "m", 2, "P"),
    (24.0, 0.5, "G", 2, None), (24.5, 0.5, "m", 2, None), (25.0, 0.5, "D", 2, None), (25.5, 0.5, "N", 2, None),
    (26.0, 1.5, "R", 3, "S"), (27.5, 0.5, "S", 3, None), (28.0, 1.0, "N", 2, None), (29.0, 1.0, "D", 2, None),
    (30.0, 2.0, "P", 2, "D"),
    (32.0, 0.5, "S", 3, None), (32.5, 0.5, "R", 3, None), (33.0, 1.0, "G", 3, "R"), (34.0, 1.0, "R", 3, None),
    (35.0, 1.0, "S", 3, None), (36.0, 1.0, "N", 2, None), (37.0, 1.0, "D", 2, None), (38.0, 1.0, "P", 2, None),
    (39.0, 1.0, "m", 2, None), (40.0, 1.0, "G", 2, None),
    (41.0, 2.0, "R", 2, "G"), (43.0, 4.0, "S", 2, "R"),
]
lead = np.zeros(N)
for b, d, sw, o, gf in MEL:
    f = hz(sw, o)
    g = hz(gf, o) if gf else None
    add(lead, b2s(b), sitar(f, d * BEAT, 1.0 if d >= 1 else 0.8, g))
# chikari-style rhythmic strums on Sa during the groove
for b in np.arange(GROOVE_IN, END, 1.0):
    add(lead, b2s(b + 0.5), sitar(hz("S", 3), 0.15, 0.25))

# ---------------------------------------------------------------- tabla: keherwa
# dha ge na ti | na ka dhi na  (8 half-beats per bar of 4 beats)
tabla = np.zeros(N)
BOLS = ["dha", "ge", "na", "ti", "na", "ka", "dhi", "na"]
for b in np.arange(GROOVE_IN, END, 0.5):
    bol = BOLS[int(((b - GROOVE_IN) * 2) % 8)]
    s = b2s(b)
    if bol in ("dha", "dhi"):
        add(tabla, s, bayan(1.0) + dayan(0.9))
    elif bol == "ge":
        add(tabla, s, bayan(0.7, glide=True))
    elif bol == "na":
        add(tabla, s, dayan(0.75))
    elif bol in ("ti", "ka"):
        add(tabla, s, dayan(0.5, open_=False))
for fb in np.arange(39.0, 41.0, 0.25):  # tihai-like run into the end card
    add(tabla, b2s(fb), dayan(0.45 + (fb - 39) * 0.2, open_=fb % 0.5 == 0))
add(tabla, b2s(END), bayan(1.3) + dayan(1.0))
for fb in (6.5, 7.0, 7.5):  # pickup into the groove
    add(tabla, b2s(fb), dayan(0.6))

# ---------------------------------------------------------------- pad
t = np.arange(N) / SR
pad = np.zeros(N)
for f, a in [(hz("S", 1), 1), (hz("P", 1), 0.6), (hz("G", 2), 0.25)]:
    for det in (-0.2, 0.2):
        ph = 2 * np.pi * f * (1 + det / 100) * t
        pad += a * (np.sin(ph) + 0.25 * np.sin(2 * ph))
pad = filt(pad, "low", 1200) * 0.045 * curve([(0, 0), (3, 0.6), (GROOVE_IN * BEAT, 0.5), (TOTAL, 0.9)])


def pan(x, p):
    return np.stack([x * np.sqrt((1 - p) / 2), x * np.sqrt((1 + p) / 2)])


mix = pan(drone * 0.5, -0.3) + pan(lead * 0.9, 0.15) + pan(tabla * 0.95, -0.05) + pan(pad, 0)
mix = np.stack([filt(mix[0], "high", 35), filt(mix[1], "high", 35)])


def ir(seed, sec=2.6):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    tt_ = np.arange(n) / SR
    x = filt(r.standard_normal(n) * np.exp(-tt_ / 0.65), "low", 6000) * np.minimum(1, tt_ / 0.012)
    return x / np.sqrt(np.sum(x ** 2))


wet = np.stack([fftconvolve(mix[0], ir(5))[:N], fftconvolve(mix[1], ir(6))[:N]])
out = (mix * 0.85 + wet * 0.45) * curve([(0, 0), (0.8, 1), (TOTAL - 1.8, 1), (TOTAL, 0)])
out /= np.max(np.abs(out)) + 1e-9
out = np.tanh(out * 1.2) / np.tanh(1.2) * 0.89
wavfile.write(OUT, SR, (out.T * 32767).astype(np.int16))
print(f"wrote {OUT}: {N / SR:.2f}s @ {BPM:.0f} BPM")
