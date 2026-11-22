#!/usr/bin/env python3
"""Build the PARVATESHA FARM Bilona ghee reel from the original clips only.

Usage:
  python3 build_reel.py <clips_dir> <fonts_dir> <work_dir> <music.wav> <output.mp4>

Every frame of footage comes from the uploaded clips. The script trims,
changes speed, regrades, adds slow push-ins and cross-fades, then overlays
gold film-style captions and a sales end card. The original sound (speech,
background noise) is dropped, and the reel runs on the music track from
make_music.py, cut to its 80 BPM beat.
"""
import glob
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

CLIPS, FONTS, WORK, MUSIC, OUT = sys.argv[1:6]
W, H, FPS = 1080, 1920, 30
BEAT = 60.0 / 80.0  # matches make_music.py
CUT = 2 / FPS       # a 2-frame micro-dissolve reads as a clean cut
os.makedirs(WORK, exist_ok=True)


def clip(prefix):
    return glob.glob(os.path.join(CLIPS, prefix + "*"))[0]


# clip, in, available-until, beats on screen, transition out, max speed,
# push-in zoom, extra crop-zoom, caption group, end-card background?
S = [
    ("c88ad34e", 0.0, 1.00, 4, 0.60, 1.00, 1.08, 1.00, 0, False),  # milk in the vessel
    ("c88ad34e", 1.8, 5.80, 4, 0.60, 0.60, 1.04, 1.00, 1, False),  # milk from the tap
    ("454f31fc", 0.0, 1.00, 4, 0.50, 1.00, 1.06, 1.00, 2, False),  # curd in the pot
    ("64f40d6b", 2.0, 4.60, 3, CUT, 0.70, 1.03, 1.00, 3, False),   # churner revealed
    ("64f40d6b", 14.0, 16.5, 2, CUT, 0.65, 1.03, 1.00, 3, False),  # hands on churner
    ("64f40d6b", 17.5, 21.0, 3, 0.60, 0.70, 1.05, 1.00, 3, False),  # churning machine
    ("36c8c524", 1.0, 2.80, 3, CUT, 0.60, 1.04, 1.00, 4, False),   # butter in the tub
    ("46d75d2b", 0.0, 3.00, 3, 0.60, 0.60, 1.04, 1.00, 4, False),  # hands with butter
    ("187ba50d", 0.0, 2.00, 3, CUT, 0.60, 1.06, 1.00, 5, False),   # butter in the pan
    ("ff3939bc", 0.3, 2.50, 2, CUT, 0.60, 1.04, 1.00, 5, False),   # melting froth
    ("5fbfb1c9", 2.0, 4.50, 3, CUT, 0.60, 1.04, 1.00, 5, False),   # turning golden
    ("e2695c1b", 1.0, 3.40, 2, 0.50, 0.60, 1.04, 1.00, 5, False),  # golden ghee
    ("8e1c51ca", 0.0, 1.80, 3, 0.90, 0.60, 1.08, 1.18, 6, False),  # finished ghee
    ("8e1c51ca", 1.2, 3.40, 7, 0.00, 1.00, 1.06, 1.18, 7, True),   # end-card background
]

CAPTIONS = {  # group: (English label, Telugu caption)
    0: ("FROM MILK TO GHEE", "పాల నుంచి నెయ్యి వరకు..."),
    1: ("FRESH COW MILK", "స్వచ్ఛమైన ఆవు పాలు"),
    2: ("NATURALLY SET CURD", "పెరుగుగా మార్చి"),
    3: ("TRADITIONAL BILONA CHURNING", "సంప్రదాయ బిలోనా పద్ధతిలో చిలికి"),
    4: ("FRESH WHITE BUTTER", "వెన్నను వేరు చేసి"),
    5: ("SLOW-COOKED GOLDEN GHEE", "నెయ్యిగా తయారు చేసి"),
}
PHONE = "+91 93905 07506"

PRE = "hqdn3d=1.5:1.5:3:3"
POST = ("unsharp=5:5:0.5:5:5:0.0,"
        "eq=contrast=1.06:brightness=-0.01:saturation=1.08:gamma=0.98,"
        "colorbalance=rs=0.03:bs=-0.04:rm=0.035:gm=0.01:bm=-0.035:rh=0.02:bh=-0.035,"
        "curves=master='0/0.025 0.25/0.22 0.5/0.5 0.75/0.79 1/0.97',"
        "vignette=angle=PI/5")


def run(cmd):
    subprocess.run(cmd, check=True)


# ------------------------------------------------------------ segments
starts, durs, files = [], [], []
t = 0.0
for i, (pre, a, avail, beats, xf, vmax, zoom, cz, g, card) in enumerate(S):
    dur = beats * BEAT + xf
    sp = min(vmax, (avail - a) / dur)
    starts.append(t)
    durs.append(dur)
    t += beats * BEAT
    vf = f"setpts=(PTS-STARTPTS)/{sp:.4f},"
    if sp < 0.97:
        vf += f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
    vf += f"fps={FPS},{PRE},"
    if cz > 1.0:  # crop away distractions at the frame edge (keeps top-centre)
        vf += f"crop=iw/{cz}:ih/{cz}:(iw-iw/{cz})/2:(ih-ih/{cz})*0.25,"
    # Slow push-in: re-scale every frame straight from the source, then crop.
    vf += (f"scale=w='2*trunc({W // 2}*(1+{zoom - 1:.3f}*t/{dur:.3f}))':h=-2:"
           f"eval=frame:flags=lanczos,crop={W}:{H},{POST}")
    if card:
        vf += ",gblur=sigma=16,eq=brightness=-0.07:saturation=0.85,vignette=angle=PI/3.6"
    vf += ",setsar=1,format=yuv420p"
    out = os.path.join(WORK, f"seg{i:02d}.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{avail - a + 0.1}", "-i", clip(pre),
         "-an", "-vf", vf, "-frames:v", str(round(dur * FPS)),
         "-c:v", "libx264", "-crf", "10", "-preset", "medium", out])
    files.append(out)
    print(f"seg{i:02d} {pre} {a:.1f}s x{sp:.2f} -> {dur:.2f}s @ {starts[-1]:.2f}s", flush=True)

TOTAL = starts[-1] + durs[-1]
END = starts[-1]  # end-card start

# ------------------------------------------------------------ caption timing
grp = {}
for i, s in enumerate(S):
    g = s[8]
    lo, hi = grp.get(g, (starts[i], starts[i] + S[i][3] * BEAT))
    grp[g] = (min(lo, starts[i]), max(hi, starts[i] + S[i][3] * BEAT))


def ts(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def rrect(w, h, r):
    """Rounded rectangle path (ASS drawing). libass anchors a drawing by its
    box from (0, 0), so coordinates stay positive and \\an5 centres it."""
    x0, y0, x1, y1 = 0, 0, w, h
    k = r * 0.45
    return (f"m {x0 + r} {y0} l {x1 - r} {y0} b {x1 - k} {y0} {x1} {y0 + k} {x1} {y0 + r} "
            f"l {x1} {y1 - r} b {x1} {y1 - k} {x1 - k} {y1} {x1 - r} {y1} "
            f"l {x0 + r} {y1} b {x0 + k} {y1} {x0} {y1 - k} {x0} {y1 - r} "
            f"l {x0} {y0 + r} b {x0} {y0 + k} {x0 + k} {y0} {x0 + r} {y0}")


# Elements: (kind, start, end, style, x, y, anim, text, shadow_blur)
# kind "gold" -> gradient-filled via mask; "cream" -> drawn directly.
E = []
CAP_Y, LAB_Y, RULE_Y = 1380, 1262, 1468
for g, (lab, tel) in CAPTIONS.items():
    lo, hi = grp[g]
    st = lo + (0.6 if g == 0 else 0.3)
    en = hi + 0.12
    d = int((en - st) * 1000)
    E.append(("cream", st + 0.15, en, "Lab", 540, LAB_Y,
              f"\\fad(650,350)\\fsp5\\t(0,{d},\\fsp10)", lab, 6))
    E.append(("gold", st, en, "Tel", 540, CAP_Y,
              f"\\move(540,{CAP_Y + 26},540,{CAP_Y},0,800)\\fad(550,350)", tel, 12))
    E.append(("gold", st + 0.25, en, "Draw", 540, RULE_Y,
              f"\\fad(250,350)\\fscx0\\t(0,900,0.6,\\fscx100)",
              "{\\p1}m 0 0 l 160 0 l 160 2.4 l 0 2.4{\\p0}", 0))

# End card
c0 = END + 0.35
E += [
    ("gold", c0, TOTAL, "Draw", 540, 598, "\\fad(600,0)\\fscx40\\t(0,900,0.5,\\fscx100)",
     "{\\p1}m 0 13 l 124 13 l 124 15 l 0 15 m 176 13 l 300 13 l 300 15 l 176 15 "
     "m 150 0 l 160 14 l 150 28 l 140 14{\\p0}", 4),
    ("gold", c0 + 0.15, TOTAL, "Brand", 540, 690,
     "\\fad(900,0)\\fsp5\\t(0,2400,0.6,\\fsp11)", "PARVATESHA FARM", 14),
    ("gold", c0 + 0.55, TOTAL, "Draw", 540, 776, "\\fad(300,0)\\fscx0\\t(0,1000,0.5,\\fscx100)",
     "{\\p1}m 0 0 l 460 0 l 460 2 l 0 2{\\p0}", 0),
    ("gold", c0 + 0.75, TOTAL, "TelB", 540, 858,
     "\\move(540,880,540,858,0,800)\\fad(700,0)", "సంప్రదాయ బిలోనా నెయ్యి", 12),
    ("cream", c0 + 1.0, TOTAL, "Lab", 540, 948, "\\fad(700,0)\\fsp4\\t(0,2500,\\fsp8)",
     "TRADITIONAL BILONA GHEE  ·  HANDMADE", 6),
    ("gold", c0 + 1.45, TOTAL, "Draw", 540, 1215, "\\fad(500,0)\\1a&HFF&\\bord2.6",
     "{\\p1}" + rrect(720, 300, 34) + "{\\p0}", 0),
    ("cream", c0 + 1.6, TOTAL, "TelS", 540, 1128, "\\fad(600,0)", "ఆర్డర్ల కోసం సంప్రదించండి", 8),
    ("gold", c0 + 1.85, TOTAL, "Phone", 540, 1220,
     "\\move(540,1240,540,1220,0,700)\\fad(600,0)", PHONE, 12),
    ("gold", c0 + 2.1, TOTAL, "Lab", 540, 1306, "\\fad(600,0)\\fsp10", "CALL  ·  WHATSAPP", 6),
    ("cream", c0 + 2.4, TOTAL, "Lab", 540, 1440, "\\fad(700,0)\\fsp12", "ORDER NOW", 6),
]

STYLES = [
    # name, font, size, spacing
    ("Tel", "Ramaraja", 112, 0),
    ("TelB", "Ramaraja", 86, 0),
    ("TelS", "Ramaraja", 60, 0),
    ("Lab", "Cormorant Garamond SemiBold", 40, 6),
    ("Brand", "Cormorant Garamond SemiBold", 92, 8),
    ("Phone", "Cormorant Garamond SemiBold", 92, 3),
    ("Draw", "Cormorant Garamond SemiBold", 20, 0),
]


def write_ass(path, kinds, colour, shadow=False):
    hdr = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
           "WrapStyle: 2", "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
           "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
           "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"]
    for n, f, sz, sp in STYLES:
        hdr.append(f"Style: {n},{f},{sz},{colour},{colour},{colour},&H00000000,0,0,0,0,"
                   f"100,100,{sp},0,1,0,0,5,0,0,0,1")
    hdr += ["", "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for kind, st, en, style, x, y, anim, text, sb in E:
        if kind not in kinds:
            continue
        pos = "" if "\\move" in anim else f"\\pos({x},{y})"
        if shadow:
            if sb == 0:
                continue
            a = anim.replace("\\1a&HFF&", "")
            tags = f"\\an5{pos}{a}\\blur{sb}\\bord{sb * 0.35:.1f}\\1a&H58&\\3a&H90&"
        else:
            tags = f"\\an5{pos}{anim}"
        hdr.append(f"Dialogue: 0,{ts(st)},{ts(en)},{style},,0,0,0,,{{{tags}}}{text}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(hdr) + "\n")


ASS_MASK = os.path.join(WORK, "gold_mask.ass")
ASS_SHADOW = os.path.join(WORK, "shadow.ass")
ASS_CREAM = os.path.join(WORK, "cream.ass")
write_ass(ASS_MASK, {"gold"}, "&H00FFFFFF")
write_ass(ASS_SHADOW, {"gold", "cream"}, "&H00000000", shadow=True)
write_ass(ASS_CREAM, {"cream"}, "&H00DCEBF7")  # warm cream #F7EBDC

# ------------------------------------------------------------ gold gradient
# Metallic gold: pale highlight at the top of each text line, deep amber below.
bands = [(CAP_Y - 62, CAP_Y + 52), (RULE_Y - 4, RULE_Y + 4), (584, 614), (640, 740),
         (770, 782), (812, 905), (1060, 1370)]
stops = np.array([0.0, 0.42, 0.5, 0.62, 1.0])
cols = np.array([[255, 240, 190], [236, 196, 108], [196, 146, 52], [214, 166, 72],
                 [246, 214, 132]], float)
grad = np.tile(np.array([226, 182, 92], float), (H, 1))
for y0, y1 in bands:
    ys = np.arange(y0, y1)
    u = (ys - y0) / max(1, (y1 - y0 - 1))
    grad[y0:y1] = np.stack([np.interp(u, stops, cols[:, c]) for c in range(3)], 1)
img = np.repeat(grad[:, None, :], W, 1)
xs = np.linspace(-1, 1, W)[None, :, None]
img *= 1 - 0.07 * xs ** 2  # slightly richer towards the edges
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(WORK, "gold.png"))
# soft dark gradient behind the caption area (and the lower frame)
yy = np.arange(H, dtype=float)
alpha = np.interp(yy, [0, 980, 1240, 1420, 1600, H], [0, 0, 0.42, 0.55, 0.45, 0.35])
grad_a = np.zeros((H, W, 4), np.uint8)
grad_a[..., 3] = (np.repeat(alpha[:, None], W, 1) * 255).astype(np.uint8)
grad_a[..., :3] = (12, 8, 4)
Image.fromarray(grad_a, "RGBA").save(os.path.join(WORK, "shade.png"))
# a soft diagonal light sweep that glides across the gold
sh = np.zeros((H, 600), np.uint8)
xx = np.arange(600)[None, :] - 300 + (np.arange(H)[:, None] - H / 2) * 0.35
sh[:] = (np.exp(-(xx / 70.0) ** 2) * 150).astype(np.uint8)
Image.fromarray(sh, "L").filter(ImageFilter.GaussianBlur(4)).save(os.path.join(WORK, "shine_a.png"))

# ------------------------------------------------------------ assemble
inp = []
for f in files:
    inp += ["-i", f]
n = len(files)
inp += ["-loop", "1", "-framerate", str(FPS), "-t", f"{TOTAL:.3f}", "-i", os.path.join(WORK, "gold.png"),
        "-loop", "1", "-framerate", str(FPS), "-t", f"{TOTAL:.3f}", "-i", os.path.join(WORK, "shine_a.png"),
        "-i", MUSIC, "-loop", "1", "-framerate", str(FPS), "-t", f"{TOTAL:.3f}",
        "-i", os.path.join(WORK, "shade.png")]
GOLD, SHINE, MUS, SHADE = n, n + 1, n + 2, n + 3

fc = []
prev = "[0:v]"
for i in range(1, n):
    xf = S[i - 1][4]
    fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={xf:.3f}:offset={starts[i]:.3f}[x{i}]")
    prev = f"[x{i}]"
# film finish: soft highlight bloom + fine moving grain
fc.append(f"{prev}format=gbrp,split[b0][b1];[b1]gblur=sigma=28[bg];"
          f"[b0][bg]blend=all_mode=screen:all_opacity=0.14,format=yuv420p,"
          f"noise=c0s=5:c0f=t+u[film0];"
          f"[{SHADE}:v]format=rgba,fade=t=out:st={END:.3f}:d=0.8:alpha=1[shade];"
          f"[film0][shade]overlay=0:0:format=auto[film]")
# gold text: gradient + moving sheen, cut out by a libass-rendered mask
fc.append(f"color=c=black:s={W}x{H}:r={FPS}:d={TOTAL:.3f},format=rgb24,"
          f"ass={ASS_MASK}:fontsdir={FONTS}:shaping=complex,format=gbrp,extractplanes=r[mask]")
fc.append(f"[{SHINE}:v]format=gray,lut=y='val'[shg];"
          f"color=c=white:s=600x{H}:r={FPS}:d={TOTAL:.3f},format=rgba[shw];"
          f"[shw][shg]alphamerge[shine];"
          f"[{GOLD}:v]format=rgba[gbase];"
          f"[gbase][shine]overlay=x='mod(t*520,{W + 2400})-900':y=0:format=auto[gsh];"
          f"[gsh]format=rgba[gsh2];[gsh2][mask]alphamerge[goldtxt]")
fc.append(f"[film]ass={ASS_SHADOW}:fontsdir={FONTS}:shaping=complex[sh];"
          f"[sh][goldtxt]overlay=0:0:format=auto,"
          f"ass={ASS_CREAM}:fontsdir={FONTS}:shaping=complex,"
          f"fade=t=in:st=0:d=0.5,fade=t=out:st={TOTAL - 0.7:.3f}:d=0.7,format=yuv420p[vout]")
fc.append(f"[{MUS}:a]atrim=0:{TOTAL:.3f},afade=t=out:st={TOTAL - 1.5:.3f}:d=1.5,"
          f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")

run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(fc),
     "-map", "[vout]", "-map", "[aout]", "-t", f"{TOTAL:.3f}",
     "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-level", "4.2",
     "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart",
     "-c:a", "aac", "-b:a", "256k", "-ar", "48000", OUT])
print(f"done: {OUT} ({TOTAL:.2f}s, end card at {END:.2f}s)")
