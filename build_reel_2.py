#!/usr/bin/env python3
"""Reel 2 for PARVATESHA FARM: a hook-first, step-by-step Bilona ghee reel.

Usage:
  python3 build_reel_2.py <clips_dir> <fonts_dir> <work_dir> <music.wav> <output.mp4>

Same rule as reel 1: every frame of footage comes from the uploaded clips. This
reel opens on the finished ghee, then walks back through five numbered steps,
with speed ramps, a butter/ghee split-screen, a brighter grade, beat-synced cuts
(96 BPM, music from make_music_2.py) and a saffron and cream end card.
"""
import glob
import os
import subprocess
import sys

import numpy as np
from PIL import Image

CLIPS, FONTS, WORK, MUSIC, OUT = sys.argv[1:6]
W, H, FPS = 1080, 1920, 30
BEAT = 60.0 / 96.0
CUT = 2 / FPS
os.makedirs(WORK, exist_ok=True)

SAFFRON, CREAM, BROWN = "&H3AA9F4&", "&HE2F4FF&", "&H08162A&"  # BGR override colours
CREAM_STYLE = "&H00E2F4FF"
PHONE = "+91 93905 07506"


def clip(prefix):
    return glob.glob(os.path.join(CLIPS, prefix + "*"))[0]


def seg(pre, a, avail, beats, tr="cut", xf=CUT, sp=1.0, ramp=None, zoom=1.05, cz=1.0,
        cy=0.25, dark=0.0, blur=0, split=None):
    return dict(pre=pre, a=a, avail=avail, beats=beats, tr=tr, xf=xf, sp=sp, ramp=ramp,
                zoom=zoom, cz=cz, cy=cy, dark=dark, blur=blur, split=split)


# tr/xf = transition INTO the next segment. ramp=(switch_at_output_s, fast, slow)
SEGS = [
    # HOOK: finished ghee first
    seg("e2695c1b", 3.5, 6.9, 3, sp=0.6, zoom=1.10, dark=0.07),
    seg("5fbfb1c9", 5.0, 9.8, 3, "fadewhite", 0.30, sp=0.6, zoom=1.06, dark=0.07),
    # 01 MILK
    seg("c88ad34e", 0.0, 0.9, 2, sp=0.5, zoom=1.10),
    seg("c88ad34e", 2.6, 5.8, 4, "smoothup", 0.35, ramp=(0.55, 1.0, 0.45), zoom=1.05),
    # 02 CURD
    seg("454f31fc", 0.0, 1.0, 4, "smoothup", 0.35, sp=0.4, zoom=1.08),
    # 03 CHURNING
    seg("64f40d6b", 0.0, 2.0, 2, sp=0.7, zoom=1.04),
    seg("454f31fc", 1.5, 4.3, 2, sp=0.8, zoom=1.04),
    seg("64f40d6b", 12.0, 14.0, 2, sp=0.8, zoom=1.04),
    seg("64f40d6b", 21.0, 24.4, 2, "smoothup", 0.35, sp=0.8, zoom=1.06),
    # 04 BUTTER
    seg("5150a18b", 0.0, 1.4, 2, ramp=(0.35, 1.0, 0.4), zoom=1.06),
    seg("46d75d2b", 8.4, 9.4, 2, sp=0.6, zoom=1.05),
    seg("187ba50d", 2.7, 5.3, 4, "smoothup", 0.35, sp=0.7, zoom=1.06),
    # 05 GHEE: butter (top) turns into ghee (bottom)
    seg(None, 0, 0, 4, sp=0.6, split=[("ff3939bc", 0.3, 2.5, 0.55, 1.0),
                                       ("8e1c51ca", 0.0, 3.4, 0.30, 1.18)]),
    seg("5fbfb1c9", 0.0, 2.0, 2, sp=0.6, zoom=1.06),
    seg("e2695c1b", 0.0, 3.0, 2, "fade", 0.40, sp=0.6, zoom=1.06),
    # value line
    seg("8e1c51ca", 0.4, 3.4, 4, "fade", 0.60, sp=0.6, zoom=1.08, cz=1.18),
    # END CARD
    seg("e2695c1b", 1.0, 3.4, 8, sp=0.4, zoom=1.06, dark=0.27, blur=20),
]

STEPS = [  # (first segment index, number, Telugu, English)
    (2, "01", "పాలు", "FRESH COW MILK"),
    (4, "02", "పెరుగు", "NATURALLY SET CURD"),
    (5, "03", "చిలకడం", "BILONA CHURNING"),
    (9, "04", "వెన్న", "WHITE BUTTER"),
    (12, "05", "నెయ్యి", "GOLDEN GHEE"),
]

PRE = "hqdn3d=1.5:1.5:3:3"
GRADE = ("unsharp=5:5:0.55:5:5:0.0,"
         "eq=contrast=1.08:brightness=0.012:saturation=1.18,"
         "colorbalance=rs=0.02:bs=-0.025:rm=0.02:bm=-0.02:rh=0.01:bh=-0.02,"
         "curves=master='0/0.01 0.25/0.23 0.5/0.51 0.75/0.79 1/0.99',"
         "vignette=angle=PI/7")


def run(cmd):
    subprocess.run(cmd, check=True)


def render(src, a, avail, dur, out, w=W, h=H, sp=1.0, ramp=None, zoom=1.05, cz=1.0,
           cy=0.25, dark=0.0, blur=0):
    if ramp:
        ts_out, s1, s2 = ramp
        need = ts_out * s1 + (dur - ts_out) * s2
        if need > avail - a:  # not enough source: slow both parts down evenly
            k = (avail - a) / need
            s1, s2 = s1 * k, s2 * k
        ta = ts_out * s1
        pts = f"setpts='(if(lt(T,{ta:.4f}),T/{s1:.4f},{ts_out:.4f}+(T-{ta:.4f})/{s2:.4f}))/TB',"
        slow = min(s1, s2) < 0.97
    else:
        sp = min(sp, (avail - a) / dur)
        pts = f"setpts=(PTS-STARTPTS)/{sp:.4f},"
        slow = sp < 0.97
    vf = pts
    if slow:
        vf += f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
    vf += f"fps={FPS},{PRE},"
    if cz > 1.0:
        vf += f"crop=iw/{cz}:ih/{cz}:(iw-iw/{cz})/2:(ih-ih/{cz})*0.25,"
    # push-in, then crop to the requested frame (cy = vertical crop anchor)
    vf += (f"scale=w='2*trunc({W // 2}*(1+{zoom - 1:.3f}*t/{dur:.3f}))':h=-2:eval=frame:flags=lanczos,"
           f"crop={w}:{h}:(iw-{w})/2:(ih-{h})*{cy},{GRADE}")
    if dark:
        vf += f",eq=brightness=-{dark}"
    if blur:
        vf += f",gblur=sigma={blur},eq=saturation=0.9,vignette=angle=PI/3.5"
    vf += ",setsar=1,format=yuv420p"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{avail - a + 0.1}", "-i", src,
         "-an", "-vf", vf, "-frames:v", str(round(dur * FPS)),
         "-c:v", "libx264", "-crf", "10", "-preset", "medium", out])


# ------------------------------------------------------------ segments
starts, durs, files = [], [], []
t = 0.0
for i, s in enumerate(SEGS):
    dur = s["beats"] * BEAT + (s["xf"] if i < len(SEGS) - 1 else 0)
    starts.append(t)
    durs.append(dur)
    t += s["beats"] * BEAT
    out = os.path.join(WORK, f"s{i:02d}.mp4")
    if os.path.exists(out) and not os.environ.get("REBUILD"):
        files.append(out)
        continue
    if s["split"]:
        halves = []
        hh = (H - 8) // 2
        for j, (pre, a, avail, cy, cz) in enumerate(s["split"]):
            hp = os.path.join(WORK, f"s{i:02d}_{j}.mp4")
            render(clip(pre), a, avail, dur, hp, h=hh, sp=s["sp"], zoom=1.06, cz=cz, cy=cy)
            halves.append(hp)
        run(["ffmpeg", "-v", "error", "-y", "-i", halves[0], "-i", halves[1], "-filter_complex",
             f"color=c=0xE2F4FF:s={W}x8:r={FPS}:d={dur:.3f}[d];[0:v][d][1:v]vstack=3,format=yuv420p",
             "-frames:v", str(round(dur * FPS)), "-c:v", "libx264", "-crf", "10", out])
    else:
        render(clip(s["pre"]), s["a"], s["avail"], dur, out, sp=s["sp"], ramp=s["ramp"],
               zoom=s["zoom"], cz=s["cz"], cy=s["cy"], dark=s["dark"], blur=s["blur"])
    files.append(out)
    print(f"s{i:02d} {s['pre'] or 'split'} -> {dur:.2f}s @ {starts[-1]:.2f}s", flush=True)

TOTAL = starts[-1] + durs[-1]
END = starts[-1]


# ------------------------------------------------------------ text (one ASS file)
def ts(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def rrect(w, h, r):
    k = r * 0.45
    return (f"m {r} 0 l {w - r} 0 b {w - k} 0 {w} {k} {w} {r} l {w} {h - r} "
            f"b {w} {h - k} {w - k} {h} {w - r} {h} l {r} {h} b {k} {h} 0 {h - k} 0 {h - r} "
            f"l 0 {r} b 0 {k} {k} 0 {r} 0")


EV = []  # (start, end, style, tags, text, shadow?)


def txt(st, en, style, tags, text, shadow=True):
    EV.append((st, en, style, tags, text, shadow))


# hook
h0, h1 = 0.25, starts[2] - 0.05
txt(h0, h1, "Lab", f"\\an5\\pos(540,560)\\fad(400,200)\\fsp6\\t(0,3000,\\fsp12)\\c{CREAM}",
    "PARVATESHA FARM")
txt(h0 + 0.1, h1, "TelHook", f"\\an5\\pos(540,850)\\fad(250,200)\\fscx70\\fscy70"
    f"\\t(0,350,0.5,\\fscx100\\fscy100)\\c{SAFFRON}", "ఈ నెయ్యి")
txt(h0 + 0.55, h1, "TelMid", f"\\an5\\move(540,1040,540,1018,0,450)\\fad(300,200)\\c{CREAM}",
    "ఎలా తయారవుతుందో చూడండి")
# steps (top-left editorial block)
for k, (si, num, tel, eng) in enumerate(STEPS):
    st = starts[si] + 0.12
    nxt = STEPS[k + 1][0] if k + 1 < len(STEPS) else 15
    en = starts[nxt] + 0.05
    txt(st, en, "Num", f"\\an4\\move(30,400,80,400,0,350)\\fad(250,250)\\c{SAFFRON}", num)
    txt(st + 0.12, en, "TelStep", f"\\an4\\move(292,414,292,392,0,400)\\fad(300,250)\\c{CREAM}", tel)
    txt(st + 0.3, en, "Lab", f"\\an7\\pos(298,478)\\fad(300,250)\\fsp4\\t(0,1500,\\fsp8)\\c{CREAM}", eng)
    txt(st + 0.2, en, "Draw", f"\\an7\\pos(84,532)\\fad(200,250)\\fscx0\\t(0,600,0.5,\\fscx100)\\c{SAFFRON}",
        "{\\p1}m 0 0 l 120 0 l 120 5 l 0 5{\\p0}", False)
# split-screen chip
sp_i = 12
c_st, c_en = starts[sp_i] + 0.4, starts[sp_i] + SEGS[sp_i]["beats"] * BEAT
txt(c_st, c_en, "Draw", f"\\an5\\pos(540,960)\\fad(200,200)\\c{BROWN}\\1a&H30&",
    "{\\p1}" + rrect(560, 120, 60) + "{\\p0}", False)
txt(c_st + 0.05, c_en, "TelChip", f"\\an5\\pos(540,958)\\fad(250,200)\\c{CREAM}",
    f"వెన్న  {{\\fnDejaVu Sans\\fs56\\c{SAFFRON}}}→{{\\fnRamabhadra\\fs104\\c{CREAM}}}  నెయ్యి", False)
# value line
v_st, v_en = starts[15] + 0.2, END + 0.1
txt(v_st, v_en, "TelMid", f"\\an5\\move(540,1392,540,1370,0,500)\\fad(350,250)\\c{CREAM}",
    "బిలోనా పద్ధతిలో తయారైన నెయ్యి")
txt(v_st + 0.35, v_en, "Lab", f"\\an5\\pos(540,1478)\\fad(400,250)\\fsp8\\c{SAFFRON}",
    "MADE THE TRADITIONAL BILONA WAY")
# end card
c0 = END + 0.3
txt(c0, TOTAL, "Brand", f"\\an5\\pos(540,620)\\fad(600,0)\\fsp2\\t(0,2000,0.6,\\fsp6)\\c{CREAM}",
    "PARVATESHA FARM")
txt(c0 + 0.3, TOTAL, "TelEnd", f"\\an5\\move(540,752,540,734,0,500)\\fad(500,0)\\c{SAFFRON}",
    "సంప్రదాయ బిలోనా నెయ్యి")
txt(c0 + 0.5, TOTAL, "Draw", f"\\an5\\pos(540,826)\\fad(200,0)\\fscx0\\t(0,700,0.5,\\fscx100)\\c{SAFFRON}",
    "{\\p1}m 0 0 l 260 0 l 260 3 l 0 3{\\p0}", False)
txt(c0 + 0.8, TOTAL, "TelS", f"\\an5\\pos(540,936)\\fad(500,0)\\c{CREAM}", "ఆర్డర్ల కోసం సంప్రదించండి")
txt(c0 + 1.0, TOTAL, "Phone", f"\\an5\\move(540,1050,540,1030,0,500)\\fad(500,0)\\c{CREAM}", PHONE)
txt(c0 + 1.2, TOTAL, "Lab", f"\\an5\\pos(540,1112)\\fad(500,0)\\fsp10\\c{CREAM}", "CALL  ·  WHATSAPP")
txt(c0 + 1.6, TOTAL, "Draw", f"\\an5\\pos(540,1250)\\fad(200,0)\\fscx60\\fscy60"
    f"\\t(0,350,0.5,\\fscx100\\fscy100)\\c{SAFFRON}", "{\\p1}" + rrect(440, 104, 52) + "{\\p0}", False)
txt(c0 + 1.7, TOTAL, "Cta", f"\\an5\\pos(540,1250)\\fad(250,0)\\fsp7\\c{BROWN}", "ORDER NOW", False)

STYLES = [  # name, font, size, bold, italic, spacing
    # Ramabhadra draws small for its size, so these are deliberately large
    ("TelHook", "Ramabhadra", 280, 0, 0, 0),
    ("TelMid", "Ramabhadra", 124, 0, 0, 0),
    ("TelStep", "Ramabhadra", 190, 0, 0, 0),
    ("TelChip", "Ramabhadra", 104, 0, 0, 0),
    ("TelEnd", "Ramabhadra", 120, 0, 0, 0),
    ("TelS", "Ramabhadra", 92, 0, 0, 0),
    ("Num", "Playfair Display", 180, -1, -1, 0),
    ("Brand", "Playfair Display SemiBold", 92, 0, 0, 2),
    ("Lab", "Montserrat", 34, -1, 0, 4),
    ("Phone", "Montserrat", 74, -1, 0, 2),
    ("Cta", "Montserrat", 38, -1, 0, 7),
    ("Draw", "Montserrat", 20, 0, 0, 0),
]
ass = os.path.join(WORK, "reel2.ass")
L = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
     "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
     "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
     "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
     "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"]
for n, f, sz, b, it, spc in STYLES:
    L.append(f"Style: {n},{f},{sz},{CREAM_STYLE},{CREAM_STYLE},&H00000000,&H00000000,{b},{it},0,0,100,100,"
             f"{spc},0,1,0,0,5,0,0,0,1")
L += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for st, en, style, tags, text, shadow in EV:
    if shadow:  # soft dark glow underneath for legibility
        base = tags.split("\\c&H")[0]
        L.append(f"Dialogue: 0,{ts(st)},{ts(en)},{style},,0,0,0,,"
                 f"{{{base}\\c&H000000&\\3c&H000000&\\bord4\\blur10\\1a&H50&\\3a&H80&}}{text}")
    L.append(f"Dialogue: 1,{ts(st)},{ts(en)},{style},,0,0,0,,{{{tags}}}{text}")
with open(ass, "w", encoding="utf-8") as fh:
    fh.write("\n".join(L) + "\n")

# top shade for the step titles (fades out before the end card)
yy = np.arange(H, dtype=float)
alpha = np.interp(yy, [0, 200, 330, 560, 760, 1250, 1500, H], [0.25, 0.42, 0.5, 0.42, 0, 0, 0.28, 0.35])
shade = np.zeros((H, W, 4), np.uint8)
shade[..., 3] = (np.repeat(alpha[:, None], W, 1) * 255).astype(np.uint8)
shade[..., :3] = (14, 8, 3)
Image.fromarray(shade, "RGBA").save(os.path.join(WORK, "shade2.png"))

# ------------------------------------------------------------ assemble
inp = []
for f in files:
    inp += ["-i", f]
n = len(files)
inp += ["-i", MUSIC, "-loop", "1", "-framerate", str(FPS), "-t", f"{TOTAL:.3f}",
        "-i", os.path.join(WORK, "shade2.png")]
MUS, SHADE = n, n + 1
fc, prev = [], "[0:v]"
for i in range(1, n):
    p = SEGS[i - 1]
    tr = "fade" if p["tr"] == "cut" else p["tr"]
    fc.append(f"{prev}[{i}:v]xfade=transition={tr}:duration={p['xf']:.3f}:offset={starts[i]:.3f}[x{i}]")
    prev = f"[x{i}]"
fc.append(f"[{SHADE}:v]format=rgba,fade=t=in:st=0:d=0.01:alpha=1,"
          f"fade=t=out:st={END - 0.4:.3f}:d=0.6:alpha=1[sh]")
fc.append(f"{prev}noise=c0s=3:c0f=t+u[v0];[v0][sh]overlay=0:0:format=auto,"
          f"ass={ass}:fontsdir={FONTS}:shaping=complex,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={TOTAL - 0.6:.3f}:d=0.6,format=yuv420p[vout]")
fc.append(f"[{MUS}:a]atrim=0:{TOTAL:.3f},afade=t=out:st={TOTAL - 1.4:.3f}:d=1.4,"
          f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(fc),
     "-map", "[vout]", "-map", "[aout]", "-t", f"{TOTAL:.3f}",
     "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-level", "4.2",
     "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart",
     "-c:a", "aac", "-b:a", "256k", "-ar", "48000", OUT])
print(f"done: {OUT} ({TOTAL:.2f}s, end card at {END:.2f}s)")
