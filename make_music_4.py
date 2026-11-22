#!/usr/bin/env python3
"""Music for reel 4: an organic, acoustic, cinematic piece at 72 BPM in D.

Fingerpicked steel-string guitar (Karplus-Strong), bowed cello, kalimba,
a soft frame-drum heartbeat, shaker, plus birdsong and wind for a farm-morning
feel. Fully synthesised here, so it is free of copyright.

Usage: python3 make_music_4.py <out.wav> [total_seconds]
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
BPM = 72.0
BEAT = 60.0 / BPM
OUT = sys.argv[1]
TOTAL = float(sys.argv[2]) if len(sys.argv) > 2 else 34.17
N = int((TOTAL + 0.2) * SR)
rng = np.random.default_rng(31)
# chapter starts in beats (match build_reel_4.py)
I, II, III, IV, V, END = 5, 11, 15, 22, 27, 34


def mid(m):  # MIDI note -> Hz
    return 440.0 * 2 ** ((m - 69) / 12)


def b2s(b):
    return int(round(b * BEAT * SR))


def filt(x, kind, fc, order=2):
    return sosfilt(butter(order, fc, kind, fs=SR, output="sos"), x)


def add(buf, start, sig, ch=None):
    if 0 <= start < buf.shape[-1]:
        e = min(buf.shape[-1], start + len(sig))
        buf[start:e] += sig[: e - start]


def curve(points):
    xs, ys = zip(*points)
    return np.interp(np.arange(N) / SR, xs, ys)


def pluck(f, vel=1.0, dur=3.5, bright=0.5):
    """Karplus-Strong string: noise burst through a tuned, damped delay loop."""
    L = max(2, int(round(SR / f)))
    n = int(dur * SR)
    x = np.zeros(n)
    burst = rng.uniform(-1, 1, L)
    burst = lfilter([bright, 1 - bright], [1], burst)  # pick position / softness
    x[:L] = burst
    a = np.zeros(L + 2)
    a[0] = 1
    a[L] = a[L + 1] = -0.4985  # loop gain < 1 gives the decay
    y = lfilter([1], a, x)
    y = filt(y, "low", 6500) * np.minimum(1, np.arange(n) / (0.002 * SR))
    return y * vel * 0.35


def cello(notes):
    """Bowed legato line: (start beat, beats, midi)."""
    s0 = b2s(notes[0][0])
    end = b2s(notes[-1][0] + notes[-1][1]) - s0
    n = end + int(0.8 * SR)
    t = np.arange(n) / SR
    f = np.zeros(n)
    prev = None
    for b, d, m in notes:
        a_, e_ = b2s(b) - s0, b2s(b + d) - s0
        tgt = mid(m)
        st = np.arange(e_ - a_) / SR
        f[a_:e_] = tgt if prev is None else prev * (tgt / prev) ** (1 - np.exp(-st / 0.06))
        f[a_:e_] *= 1 + np.clip((st - 0.3) / 0.6, 0, 1) * 0.004 * np.sin(2 * np.pi * 5.2 * st)
        prev = tgt
    f[end:] = prev
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = sum(np.sin(k * ph) / k for k in range(1, 14))
    env = np.minimum(1, t / 0.6) * np.clip(1 - (t - end / SR) / 0.7, 0, 1)
    env *= 1 + 0.04 * filt(rng.standard_normal(n), "low", 4)  # bow pressure
    bow = filt(rng.standard_normal(n), "band", [1500, 5000]) * 0.03
    sig = filt(tone * 0.25 + bow, "band", [70, 2400]) * env
    return s0, sig * 0.5


def kalimba(f, vel=1.0):
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.6) + 0.25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.08)
    return s * np.minimum(1, t / 0.002) * vel * 0.14


def heartbeat(vel=1.0):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 52 + 30 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2) * vel * 0.5


def shaker(vel=1.0):
    n = int(0.15 * SR)
    t = np.arange(n) / SR
    return filt(rng.standard_normal(n), "high", 4500) * np.minimum(1, t / 0.02) * np.exp(-t / 0.05) * vel * 0.05


def bird(f0=3800, notes=4):
    seg = int(0.075 * SR)
    out = np.zeros(seg * notes + int(0.2 * SR))
    for k in range(notes):
        t = np.arange(seg) / SR
        f = f0 * (1 + 0.35 * np.sin(np.pi * t / t[-1])) * (1 + rng.uniform(-0.08, 0.08))
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / t[-1]) ** 2
        out[k * seg + int(k * 0.02 * SR): k * seg + int(k * 0.02 * SR) + seg] += s
    return filt(out, "band", [2000, 9000]) * 0.05


# ---------------------------------------------------------------- guitar
# one chord per bar: Dadd9, Gmaj7/D, Bm7, Asus4 -> A
CHORDS = [
    [50, 57, 64, 66, 69],  # D3 A3 E4 F#4 A4
    [43, 50, 59, 66, 62],  # G2 D3 B3 F#4 D4
    [47, 54, 57, 62, 66],  # B2 F#3 A3 D4 F#4
    [45, 52, 57, 62, 64],  # A2 E3 A3 D4 E4
]
PATTERN = [0, 2, 3, 4, 2, 3, 4, 3]  # string order per 8th note
guitar = np.zeros(N)
for b in np.arange(0, END, 0.5):
    bar = int(b // 4)
    ch = CHORDS[bar % 4]
    j = int((b % 4) * 2)
    if b < I and j % 2:  # intro: only on the beat
        continue
    m = ch[PATTERN[j]]
    if bar % 4 == 3 and j >= 4 and PATTERN[j] == 3:
        m = 61  # sus4 resolves to C#4
    vel = (1.0 if j == 0 else 0.62) * (1.0 if b < I else 0.9)
    add(guitar, b2s(b) + int(rng.uniform(0, 0.012) * SR), pluck(mid(m), vel, bright=0.35 if j == 0 else 0.55))
# ending: slow strum of Dadd9, then a high harmonic
for k, m in enumerate([50, 57, 62, 66, 69, 74]):
    add(guitar, b2s(END) + int(k * 0.045 * SR), pluck(mid(m), 0.9, dur=6.0))
add(guitar, b2s(END + 4), pluck(mid(78), 0.5, dur=5.0, bright=0.9))

# ---------------------------------------------------------------- cello
cel = np.zeros(N)
for phrase in [
    [(I, 3.0, 54), (I + 3, 1.0, 57), (I + 4, 4.0, 59), (I + 8, 2.0, 57)],
    [(III, 2.0, 50), (III + 2, 2.0, 54), (III + 4, 3.0, 57)],
    [(IV + 1, 4.0, 62), (IV + 5, 1.0, 61)],
    [(V, 2.0, 59), (V + 2, 2.0, 62), (V + 4, 1.0, 64), (V + 5, 2.0, 66)],
    [(END, 6.0, 50)],
]:
    s0, sig = cello(phrase)
    add(cel, s0, sig)

# ---------------------------------------------------------------- kalimba (butter & ghee)
kal = np.zeros(N)
for b, m in [(IV, 74), (IV + 0.5, 78), (IV + 1, 81), (IV + 2, 78), (IV + 3, 76), (IV + 3.5, 74),
             (V, 81), (V + 1, 78), (V + 1.5, 76), (V + 2, 74), (V + 3, 76), (V + 4, 78), (V + 6, 81),
             (END + 1, 86), (END + 1.5, 81), (END + 2, 78)]:
    add(kal, b2s(b), kalimba(mid(m), 0.9))

# ---------------------------------------------------------------- percussion
perc = np.zeros(N)
for b in np.arange(III, END, 1.0):
    if b % 4 == 0:
        add(perc, b2s(b), heartbeat(1.0))
        add(perc, b2s(b + 0.35), heartbeat(0.55))
for b in np.arange(III, END, 0.5):
    add(perc, b2s(b), shaker(1.0 if b % 1 else 0.6))
add(perc, b2s(END), heartbeat(1.2))

# ---------------------------------------------------------------- ambience
amb = np.zeros(N)
for tb in [0.3, 1.6, 2.9, 4.1, 8.0, 13.5, END * BEAT + 0.8, END * BEAT + 2.6, END * BEAT + 4.2]:
    if tb < TOTAL - 0.5:
        add(amb, int(tb * SR), bird(rng.uniform(3200, 4600), int(rng.integers(3, 6))))
wind = filt(rng.standard_normal(N), "band", [180, 1400]) * 0.025
wind *= (0.6 + 0.4 * filt(rng.standard_normal(N), "low", 0.3) / 0.02).clip(0.2, 1.6)
amb += wind * curve([(0, 1), (I * BEAT, 0.5), (END * BEAT, 0.4), (TOTAL, 0.9)])


def pan(x, p):
    return np.stack([x * np.sqrt((1 - p) / 2), x * np.sqrt((1 + p) / 2)])


mix = (pan(guitar * 1.0, -0.2) + pan(cel * 0.45, 0.15) + pan(kal, 0.35)
       + pan(perc * 0.55, 0.0) + pan(amb, 0.45) * 0.7 + pan(np.roll(amb, 2400), -0.45) * 0.7)
mix = np.stack([filt(mix[0], "high", 30), filt(mix[1], "high", 30)])


def ir(seed, sec=3.0):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    tt = np.arange(n) / SR
    x = filt(r.standard_normal(n) * np.exp(-tt / 0.8), "low", 5500) * np.minimum(1, tt / 0.015)
    return x / np.sqrt(np.sum(x ** 2))


wet = np.stack([fftconvolve(mix[0], ir(7))[:N], fftconvolve(mix[1], ir(8))[:N]])
out = (mix * 0.8 + wet * 0.5) * curve([(0, 0), (1.0, 1), (TOTAL - 2.0, 1), (TOTAL, 0)])
out /= np.max(np.abs(out)) + 1e-9
out = np.tanh(out * 1.15) / np.tanh(1.15) * 0.89
wavfile.write(OUT, SR, (out.T * 32767).astype(np.int16))
print(f"wrote {OUT}: {N / SR:.2f}s @ {BPM:.0f} BPM")
