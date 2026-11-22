#!/usr/bin/env python3
"""10-second cinematic bumper sting for reel 5 (96 BPM grid, key of D).

Deep boom, santoor sparkle, drum hits on every cut, a rising swell, then a
big impact with tanpura, a cello chord and a bansuri-style flute motif under
the brand. Fully synthesised here, so it is free of copyright.

Usage: python3 make_music_5.py <out.wav> [total_seconds]
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
BEAT = 60.0 / 96.0
OUT = sys.argv[1]
TOTAL = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
N = int((TOTAL + 0.1) * SR)
rng = np.random.default_rng(41)
HIT = 10 * BEAT  # 6.25 s: brand impact
D3 = 146.83


def filt(x, kind, fc, order=2):
    return sosfilt(butter(order, fc, kind, fs=SR, output="sos"), x)


def add(buf, t, sig):
    s = int(t * SR)
    if 0 <= s < len(buf):
        e = min(len(buf), s + len(sig))
        buf[s:e] += sig[: e - s]


def boom(vel=1.0, dur=2.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 38 + 60 * np.exp(-t / 0.06)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    click = filt(rng.standard_normal(n), "low", 2500) * np.exp(-t / 0.015) * 0.5
    return (body + click) * vel


def drum(vel=1.0):
    n = int(0.7 * SR)
    t = np.arange(n) / SR
    f = 62 + 70 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.25)
    skin = filt(rng.standard_normal(n), "band", [300, 3000]) * np.exp(-t / 0.03) * 0.5
    return (body + skin) * vel * 0.6


def santoor(f, vel=1.0, dur=2.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = sum((1 / k) * np.exp(-t * (2 + k)) * np.sin(2 * np.pi * f * k * (1 + 0.0008 * k * k) * t)
              for k in range(1, 8))
    return out * np.minimum(1, t / 0.002) * vel * 0.16


def tanpura_chord(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f, a in [(D3 / 2, 1.0), (D3 * 0.75, 0.7), (D3, 0.8), (D3 * 1.5, 0.5), (D3 * 2, 0.4), (D3 * 2.5, 0.25)]:
        for k in range(1, 10):
            out += a / k * np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6.28)) * np.exp(-t * (0.25 + 0.08 * k))
    return filt(out, "low", 3000) * np.minimum(1, t / 0.01) * 0.08


def flute(notes):
    """notes: list of (start_s, dur_s, freq)."""
    t0 = notes[0][0]
    end = notes[-1][0] + notes[-1][1] - t0
    n = int((end + 0.5) * SR)
    t = np.arange(n) / SR
    f = np.zeros(n)
    prev = None
    for s, d, fr in notes:
        a, b = int((s - t0) * SR), int((s - t0 + d) * SR)
        st = np.arange(b - a) / SR
        f[a:b] = fr if prev is None else prev * (fr / prev) ** (1 - np.exp(-st / 0.04))
        f[a:b] *= 1 + np.clip((st - 0.25) / 0.4, 0, 1) * 0.006 * np.sin(2 * np.pi * 5.2 * st)
        prev = fr
    f[int(end * SR):] = prev
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.minimum(1, t / 0.1) * np.clip(1 - (t - end) / 0.4, 0, 1)
    tone = np.sin(ph) + 0.2 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    breath = filt(rng.standard_normal(n), "band", [900, 5000]) * 0.1
    return t0, filt((tone + breath) * env, "low", 6500) * 0.3


mix = np.zeros(N)
# opening boom + sparkle
add(mix, 0.0, boom(0.9))
for k, m in enumerate([1, 1.5, 2, 3, 4]):
    add(mix, 0.05 + k * 0.09, santoor(D3 * m, 0.8))
# drum hit on every cut (every 2 beats), building
for k in range(1, 5):
    add(mix, k * 2 * BEAT, drum(0.55 + 0.12 * k))
    add(mix, k * 2 * BEAT + BEAT, drum(0.3 + 0.06 * k))
# santoor pulse under the cuts
pat = [1, 1.5, 2, 1.5, 1.25, 1.5, 2, 2.5]
for j, b in enumerate(np.arange(0, 10, 0.5)):
    add(mix, b * BEAT, santoor(D3 * 2 * pat[j % 8], 0.55 if j % 2 else 0.8, 1.2))
# rising swell into the hit
n = int(HIT * SR)
t = np.arange(n) / SR
swell = filt(rng.standard_normal(n), "band", [500, 8000]) * (np.clip((t - 3.0) / (HIT - 3.0), 0, 1) ** 2.5) * 0.25
add(mix, 0.0, swell)
# THE HIT: boom, cymbal-ish wash, chord, flute motif
add(mix, HIT, boom(1.3, 3.5))
n = int(3.0 * SR)
t = np.arange(n) / SR
add(mix, HIT, filt(rng.standard_normal(n), "high", 3000) * np.exp(-t / 0.9) * 0.18)
add(mix, HIT, tanpura_chord(TOTAL - HIT + 0.5))
for k, m in enumerate([4, 3, 2.5, 2, 1.5, 1]):
    add(mix, HIT + 0.15 + k * 0.12, santoor(D3 * m, 0.6, 2.5))
s0, fl = flute([(HIT + 0.4, 0.45, D3 * 2 * 1.25), (HIT + 0.85, 0.45, D3 * 2 * 1.5),
                (HIT + 1.3, 2.3, D3 * 2)])
add(mix, s0, fl)

mix = filt(mix, "high", 25)
stereo = np.stack([mix, np.roll(mix, 180)])


def ir(seed, sec=2.6):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    tt = np.arange(n) / SR
    x = filt(r.standard_normal(n) * np.exp(-tt / 0.7), "low", 6000) * np.minimum(1, tt / 0.01)
    return x / np.sqrt(np.sum(x ** 2))


wet = np.stack([fftconvolve(stereo[0], ir(1))[:N], fftconvolve(stereo[1], ir(2))[:N]])
out = stereo * 0.85 + wet * 0.45
tt = np.arange(N) / SR
out *= np.interp(tt, [0, 0.02, TOTAL - 0.9, TOTAL], [0, 1, 1, 0])
out /= np.max(np.abs(out)) + 1e-9
out = np.tanh(out * 1.3) / np.tanh(1.3) * 0.89
wavfile.write(OUT, SR, (out.T * 32767).astype(np.int16))
print(f"wrote {OUT}: {N / SR:.2f}s")
