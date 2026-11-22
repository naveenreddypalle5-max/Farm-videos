#!/usr/bin/env python3
"""Music for reel 2: a bright Indian folk-style groove, 96 BPM, in E.

Santoor riff, bansuri-style flute hook, dholak, shaker, bass drone and hall
reverb. Fully synthesised here, so it is free of copyright.

Usage: python3 make_music_2.py <out.wav> [total_seconds]
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
BPM = 96.0
BEAT = 60.0 / BPM
OUT = sys.argv[1]
TOTAL = float(sys.argv[2]) if len(sys.argv) > 2 else 32.5
N = int((TOTAL + 0.2) * SR)
rng = np.random.default_rng(11)

SA = 164.81  # E3
RATIO = {"S": 1.0, "R": 9 / 8, "G": 5 / 4, "M": 4 / 3, "P": 3 / 2, "D": 5 / 3, "N": 15 / 8}


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


# Sections (beats): hook 0-6, steps 6-44, end card 44-52
HOOK_END, END = 6, 44


# ---------------------------------------------------------------- instruments
def santoor(f, vel=1.0, dur=1.8):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 9):
        fk = f * k * (1 + 0.0008 * k * k)
        if fk > 12000:
            break
        for det in (-0.7, 0.7):
            out += (1 / k) * np.exp(-t * (2.2 + 1.0 * k)) * np.sin(2 * np.pi * (fk + det) * t)
    return out * np.minimum(1, t / 0.002) * vel * 0.16


def flute_phrase(notes):
    s0 = b2s(notes[0][0])
    end = b2s(notes[-1][0] + notes[-1][1]) - s0
    n = end + int(0.45 * SR)
    t = np.arange(n) / SR
    f = np.zeros(n)
    amp = np.zeros(n)
    prev = None
    for sb, db, sw, o in notes:
        a, b = b2s(sb) - s0, b2s(sb + db) - s0
        tgt = hz(sw, o)
        st = np.arange(b - a) / SR
        f[a:b] = tgt if prev is None else prev * (tgt / prev) ** (1 - np.exp(-st / 0.035))
        f[a:b] *= 1 + np.clip((st - 0.2) / 0.4, 0, 1) * 0.005 * np.sin(2 * np.pi * 5.4 * st)
        amp[a:b] = (1 - 0.3 * np.exp(-st / 0.04)) if prev is not None else 1
        prev = tgt
    f[end:] = prev
    env = np.minimum(1, t / 0.08) * np.where(t > end / SR, np.clip(1 - (t - end / SR) / 0.3, 0, 1), 1)
    amp[end:] = 1
    amp *= env * (1 + 0.03 * filt(rng.standard_normal(n), "low", 6))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) + 0.2 * np.sin(2 * ph + 0.3) + 0.08 * np.sin(3 * ph + 1.1)
    breath = filt(rng.standard_normal(n), "band", [1000, 5500]) * 0.1
    return s0, filt((tone + breath) * amp, "low", 7000)


def dhol_low(vel=1.0, bend=True):  # dholak bass head ("dha"/"ge")
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 75 + 55 * np.exp(-t / 0.025) + (18 * (1 - np.exp(-t / 0.08)) if bend else 0)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
    return (body + filt(rng.standard_normal(n), "low", 1200) * np.exp(-t / 0.01) * 0.35) * vel * 0.6


def dhol_high(vel=1.0):  # treble head ("na"/"tin")
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    ring = (np.sin(2 * np.pi * 520 * t) + 0.5 * np.sin(2 * np.pi * 1180 * t)) * np.exp(-t / 0.06)
    snap = filt(rng.standard_normal(n), "band", [1800, 7000]) * np.exp(-t / 0.012)
    return (ring * 0.45 + snap) * vel * 0.25


def shaker(vel=1.0):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    x = filt(rng.standard_normal(n), "high", 5000) * np.minimum(1, t / 0.01) * np.exp(-t / 0.035)
    return x * vel * 0.09


# ---------------------------------------------------------------- score
plucks = np.zeros(N)
RIFF = [("S", 2), ("G", 2), ("P", 2), ("S", 3), ("P", 2), ("G", 2), ("D", 2), ("P", 2)]
RIFF_B = [("S", 2), ("R", 2), ("G", 2), ("P", 2), ("D", 2), ("P", 2), ("G", 2), ("R", 2)]
for beat in np.arange(0, END, 0.5):
    bar = int(beat // 4)
    j = int((beat % 4) * 2)
    riff = RIFF_B if bar % 2 else RIFF
    sw, o = riff[j]
    if beat < HOOK_END and j % 2:
        continue  # sparser in the hook
    vel = (0.95 if j % 2 == 0 else 0.6) * (0.7 if beat < HOOK_END else 1.0)
    add(plucks, b2s(beat), santoor(hz(sw, o), vel))
for j, (sw, o) in enumerate([("S", 3), ("D", 2), ("P", 2), ("G", 2), ("R", 2), ("S", 2)]):
    add(plucks, b2s(END + j * 0.5), santoor(hz(sw, o), 0.8, dur=3.0))
add(plucks, b2s(END + 4), santoor(hz("S", 1), 0.8, dur=3.5))

flute = np.zeros(N)
PHRASES = [
    [(0.0, 1.0, "G", 2), (1.0, 0.5, "P", 2), (1.5, 2.5, "S", 3)],  # hook call
    [(6.0, 0.5, "S", 2), (6.5, 0.5, "G", 2), (7.0, 1.0, "P", 2), (8.0, 0.5, "D", 2),
     (8.5, 0.5, "P", 2), (9.0, 1.0, "G", 2), (10.0, 2.0, "R", 2)],
    [(14.0, 0.5, "G", 2), (14.5, 0.5, "P", 2), (15.0, 1.0, "D", 2), (16.0, 1.0, "S", 3),
     (17.0, 0.5, "D", 2), (17.5, 0.5, "P", 2), (18.0, 2.0, "G", 2)],
    [(22.0, 0.5, "P", 2), (22.5, 0.5, "D", 2), (23.0, 1.0, "S", 3), (24.0, 1.0, "R", 3),
     (25.0, 1.0, "S", 3), (26.0, 2.0, "D", 2)],
    [(30.0, 0.5, "S", 3), (30.5, 0.5, "R", 3), (31.0, 1.0, "G", 3), (32.0, 1.0, "R", 3),
     (33.0, 0.5, "S", 3), (33.5, 0.5, "D", 2), (34.0, 2.0, "S", 3)],
    [(38.0, 0.5, "P", 2), (38.5, 0.5, "D", 2), (39.0, 1.0, "S", 3), (40.0, 1.0, "D", 2),
     (41.0, 1.0, "P", 2), (42.0, 1.0, "G", 2), (43.0, 1.0, "R", 2)],
    [(44.0, 6.5, "S", 2)],
]
for ph in PHRASES:
    s0, sig = flute_phrase(ph)
    add(flute, s0, sig)

drums = np.zeros(N)
for beat in np.arange(HOOK_END, END, 0.5):
    p = beat % 4
    if p in (0.0, 2.5):
        add(drums, b2s(beat), dhol_low(1.0 if p == 0 else 0.75))
    if p in (1.5, 3.5):
        add(drums, b2s(beat), dhol_low(0.45, bend=False))
    if p in (1.0, 3.0):
        add(drums, b2s(beat), dhol_high(0.9))
    if p in (0.5, 2.0):
        add(drums, b2s(beat), dhol_high(0.45))
for beat in np.arange(0, END, 0.25):  # shaker 16ths after the hook
    if beat >= HOOK_END:
        add(drums, b2s(beat), shaker(1.0 if (beat * 4) % 2 == 0 else 0.55))
for fb in (5.0, 5.25, 5.5, 5.75):  # fill out of the hook
    add(drums, b2s(fb), dhol_high(0.5 + (fb - 5) * 0.6))
add(drums, b2s(HOOK_END), dhol_low(1.3))
for fb in (42.5, 42.75, 43.0, 43.25, 43.5, 43.75):  # fill into the end card
    add(drums, b2s(fb), dhol_high(0.5 + (fb - 42.5) * 0.35))
add(drums, b2s(END), dhol_low(1.4))

t = np.arange(N) / SR
bass = np.zeros(N)
for f, a in [(hz("S", 0), 1.0), (hz("P", 0), 0.5), (hz("S", 1), 0.35)]:
    ph = 2 * np.pi * f * t + rng.uniform(0, 6.28)
    bass += a * (np.sin(ph) + 0.25 * np.sin(2 * ph))
bass = filt(bass, "low", 900) * 0.07 * curve([(0, 0.4), (HOOK_END * BEAT, 1.0), (TOTAL, 0.8)])

riser = filt(rng.standard_normal(N), "band", [800, 8000]) * 0.07
riser *= curve([(0, 0), (3.0 * BEAT, 0), (HOOK_END * BEAT - 0.03, 1), (HOOK_END * BEAT, 0),
                (41 * BEAT, 0), (END * BEAT - 0.03, 0.8), (END * BEAT, 0), (TOTAL, 0)]) ** 2


def pan(x, p):
    return np.stack([x * np.sqrt((1 - p) / 2), x * np.sqrt((1 + p) / 2)])


mix = (pan(plucks * 0.8, 0.28) + pan(flute * 0.4, -0.1) + pan(drums * 0.9, 0.0)
       + pan(bass, 0.0) + pan(riser, 0.0))
mix = np.stack([filt(mix[0], "high", 35), filt(mix[1], "high", 35)])


def ir(seed, sec=2.2):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    tt = np.arange(n) / SR
    x = filt(r.standard_normal(n) * np.exp(-tt / 0.55), "low", 6500) * np.minimum(1, tt / 0.01)
    return x / np.sqrt(np.sum(x ** 2))


wet = np.stack([fftconvolve(mix[0], ir(3))[:N], fftconvolve(mix[1], ir(4))[:N]])
out = (mix * 0.85 + wet * 0.42) * curve([(0, 0), (0.3, 1), (TOTAL - 1.6, 1), (TOTAL, 0)])
out /= np.max(np.abs(out)) + 1e-9
out = np.tanh(out * 1.25) / np.tanh(1.25) * 0.89
wavfile.write(OUT, SR, (out.T * 32767).astype(np.int16))
print(f"wrote {OUT}: {N / SR:.2f}s @ {BPM:.0f} BPM")
