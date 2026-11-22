#!/usr/bin/env python3
"""Reel 3 for PARVATESHA FARM: natural colour + kinetic typography.

Usage:
  python3 build_reel_3.py <clips_dir> <fonts_dir> <work_dir> <music.wav> <output.mp4>

Footage keeps its original colours: no grade, LUT, vignette or grain. Clips
are only trimmed, slowed, upscaled (with a light sharpen) and given slow
push-ins. The design work is in the text: highlighter bars that wipe in, Telugu
words rising out of them one by one, English lines typing in letter by letter,
a brand title that tightens into place, and a cream end card with the ghee in
a round window and the phone number typing itself out. Cuts follow the
88 BPM music from make_music_3.py.
"""
import glob
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CLIPS, FONTS, WORK, MUSIC, OUT = sys.argv[1:6]
W, H, FPS = 1080, 1920, 30
BEAT = 60.0 / 88.0
CUT = 2 / FPS
os.makedirs(WORK, exist_ok=True)
PHONE = "+91 93905 07506"

# override colours (ASS BGR)
WHITE, DARK, GOLD, GREEN, CREAM = "&HFFFFFF&", "&H12243B&", "&H1F79B7&", "&H3A5D2F&", "&HE1F0F7&"
BAR = {  # highlighter colour per scene: milk white -> butter yellow -> ghee gold
    "milk": "&HE6F6FF&", "curd": "&HD8F0FF&", "churn": "&H9CD8FF&",
    "butter": "&H4FD5FF&", "ghee": "&H3AB5F2&",
}
TEL_FONT, TEL_SIZE = "Sree Krushnadevaraya", 176  # this font draws small for its size


def clip(prefix):
    return glob.glob(os.path.join(CLIPS, prefix + "*"))[0]


def run(cmd):
    subprocess.run(cmd, check=True)


# (clip, in, available-until, beats, transition-out, xf, max speed, zoom, crop-zoom)
SEGS = [
    ("c88ad34e", 0.0, 1.0, 4, "zoomin", 0.50, 1.0, 1.08, 1.0),      # 0 milk in the vessel
    ("c88ad34e", 1.8, 5.8, 4, "circleopen", 0.50, 0.65, 1.04, 1.0),  # 1 milk from the tap
    ("454f31fc", 0.0, 1.0, 4, "zoomin", 0.50, 1.0, 1.08, 1.0),       # 2 curd in the pot
    ("64f40d6b", 17.5, 21.0, 2, "cut", CUT, 0.7, 1.04, 1.0),         # 3 churning machine
    ("64f40d6b", 4.5, 7.0, 2, "cut", CUT, 0.7, 1.04, 1.0),           # 4 hand at the churner
    ("454f31fc", 2.5, 4.3, 2, "cut", CUT, 0.7, 1.04, 1.0),           # 5 lid and churner
    ("64f40d6b", 21.0, 24.4, 2, "fade", 0.40, 0.8, 1.05, 1.0),       # 6 machines at work
    ("36c8c524", 0.0, 2.8, 3, "cut", CUT, 0.7, 1.04, 1.0),           # 7 butter into the tub
    ("46d75d2b", 3.0, 5.6, 3, "cut", CUT, 0.65, 1.04, 1.0),          # 8 butter in hand
    ("5150a18b", 2.7, 4.3, 2, "zoomin", 0.50, 0.65, 1.05, 1.0),      # 9 pressing butter
    ("187ba50d", 0.0, 2.0, 3, "cut", CUT, 0.65, 1.06, 1.0),          # 10 butter in the pan
    ("ff3939bc", 2.5, 6.0, 3, "fade", 0.40, 0.7, 1.05, 1.0),         # 11 melting froth
    ("5fbfb1c9", 0.0, 2.0, 2, "cut", CUT, 0.6, 1.05, 1.0),           # 12 turning golden
    ("e2695c1b", 0.0, 3.4, 2, "cut", CUT, 0.6, 1.05, 1.0),           # 13 golden ghee
    ("8e1c51ca", 0.0, 3.4, 3, "circleclose", 0.70, 0.6, 1.08, 1.18),  # 14 finished ghee
]
CARD_BEATS = 8

SCENES = [  # (first seg, last seg, bar colour, Telugu, English)
    (0, 0, "milk", "పాల నుంచి నెయ్యి వరకు", None),
    (1, 1, "milk", "స్వచ్ఛమైన ఆవు పాలు", "PURE COW MILK"),
    (2, 2, "curd", "తోడు పెట్టిన పెరుగు", "NATURALLY SET CURD"),
    (3, 6, "churn", "బిలోనా పద్ధతిలో చిలికి", "CHURNED THE BILONA WAY"),
    (7, 9, "butter", "తాజా వెన్న", "FRESH WHITE BUTTER"),
    (10, 11, "butter", "నెమ్మదిగా కాచిన నెయ్యి", "SLOW-COOKED"),
    (12, 14, "ghee", "బంగారు రంగు, కమ్మని సువాసన", "GOLDEN COLOUR  ·  RICH AROMA"),
]

# light denoise + upscale + sharpen only: no colour changes
PRE = "hqdn3d=1.2:1.2:2.5:2.5"
SHARP = "unsharp=5:5:0.45:5:5:0.0"


def render(src, a, avail, dur, out, sp, zoom, cz):
    sp = min(sp, (avail - a) / dur)
    vf = f"setpts=(PTS-STARTPTS)/{sp:.4f},"
    if sp < 0.97:
        vf += f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
    vf += f"fps={FPS},{PRE},"
    if cz > 1.0:
        vf += f"crop=iw/{cz}:ih/{cz}:(iw-iw/{cz})/2:(ih-ih/{cz})*0.25,"
    vf += (f"scale=w='2*trunc({W // 2}*(1+{zoom - 1:.3f}*t/{dur:.3f}))':h=-2:eval=frame:flags=lanczos,"
           f"crop={W}:{H},{SHARP},setsar=1,format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{avail - a + 0.1}", "-i", src,
         "-an", "-vf", vf, "-frames:v", str(round(dur * FPS)),
         "-c:v", "libx264", "-crf", "10", "-preset", "medium", out])


# ------------------------------------------------------------ footage segments
starts, durs, files = [], [], []
t = 0.0
for i, (pre, a, avail, beats, tr, xf, sp, zoom, cz) in enumerate(SEGS):
    dur = beats * BEAT + xf
    starts.append(t)
    durs.append(dur)
    t += beats * BEAT
    out = os.path.join(WORK, f"s{i:02d}.mp4")
    if not (os.path.exists(out) and not os.environ.get("REBUILD")):
        render(clip(pre), a, avail, dur, out, sp, zoom, cz)
    files.append(out)
    print(f"s{i:02d} {pre} -> {dur:.2f}s @ {starts[-1]:.2f}s", flush=True)
END = t
CARD_DUR = CARD_BEATS * BEAT
TOTAL = END + CARD_DUR

# ------------------------------------------------------------ end card background
# cream paper, thin gold frame, golden ghee in a round window
CIRC_D, CIRC_CX, CIRC_CY = 520, 540, 560
mask = Image.new("L", (CIRC_D * 4, CIRC_D * 4), 0)
ImageDraw.Draw(mask).ellipse((0, 0, CIRC_D * 4 - 1, CIRC_D * 4 - 1), fill=255)
mask.resize((CIRC_D, CIRC_D), Image.LANCZOS).save(os.path.join(WORK, "circle.png"))
paper = np.zeros((H, W, 3), float)
paper[:] = (247, 240, 225)
yy, xx = np.mgrid[0:H, 0:W]
paper *= (1 - 0.06 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2))[..., None]
Image.fromarray(paper.clip(0, 255).astype(np.uint8)).save(os.path.join(WORK, "paper.png"))
card_src = os.path.join(WORK, "card_ghee.mp4")
if not (os.path.exists(card_src) and not os.environ.get("REBUILD")):
    render(clip("8e1c51ca"), 0.6, 3.4, CARD_DUR, card_src, 0.5, 1.06, 1.18)
card = os.path.join(WORK, "card.mp4")
run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{CARD_DUR:.3f}",
     "-i", os.path.join(WORK, "paper.png"), "-i", card_src, "-loop", "1", "-framerate", str(FPS),
     "-t", f"{CARD_DUR:.3f}", "-i", os.path.join(WORK, "circle.png"), "-filter_complex",
     f"[1:v]crop=iw:iw:0:(ih-iw)*0.35,scale={CIRC_D}:{CIRC_D},format=rgba[g];"
     f"[2:v]format=gray[m];[g][m]alphamerge[gc];"
     f"[0:v][gc]overlay={CIRC_CX - CIRC_D // 2}:{CIRC_CY - CIRC_D // 2}:format=auto,format=yuv420p",
     "-frames:v", str(round(CARD_DUR * FPS)), "-c:v", "libx264", "-crf", "10", card])


# ------------------------------------------------------------ measure Telugu lines with libass
def measure(text, font, size):
    a = os.path.join(WORK, "measure.ass")
    with open(a, "w", encoding="utf-8") as fh:
        fh.write("[Script Info]\nPlayResX: 1080\nPlayResY: 600\nWrapStyle: 2\n\n[V4+ Styles]\n"
                 "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
                 "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
                 "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                 f"Style: M,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,"
                 "100,100,0,0,1,0,0,5,0,0,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, "
                 f"MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:00.00,0:00:01.00,M,,0,0,0,,"
                 f"{{\\pos(540,300)}}{text}\n")
    png = os.path.join(WORK, "measure.png")
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x600:d=1",
         "-vf", f"ass={a}:fontsdir={FONTS}:shaping=complex", "-frames:v", "1", png])
    arr = np.asarray(Image.open(png).convert("L"))
    ys, xs = np.where(arr > 60)
    return xs.max() - xs.min() + 1, ys.max() - ys.min() + 1, (ys.max() + ys.min()) / 2 - 300


def ts(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def rrect(w, h, r):
    k = r * 0.45
    return (f"m {r} 0 l {w - r} 0 b {w - k} 0 {w} {k} {w} {r} l {w} {h - r} "
            f"b {w} {h - k} {w - k} {h} {w - r} {h} l {r} {h} b {k} {h} 0 {h - k} 0 {h - r} "
            f"l 0 {r} b 0 {k} {k} 0 {r} 0")


def circle(d):
    """Circle path of diameter d (four Bezier quadrants), box from (0, 0)."""
    r, k = d / 2, d / 2 * 0.5523
    return (f"m {d} {r} b {d} {r + k} {r + k} {d} {r} {d} b {r - k} {d} 0 {r + k} 0 {r} "
            f"b 0 {r - k} {r - k} 0 {r} 0 b {r + k} 0 {d} {r - k} {d} {r}")


EV = []


def ev(layer, st, en, style, tags, text):
    EV.append(f"Dialogue: {layer},{ts(st)},{ts(en)},{style},,0,0,0,,{{{tags}}}{text}")


def per_letter(text, t0, step, extra_from="", extra_to=""):
    """Each letter fades/sharpens in, staggered: a typewriter-style reveal."""
    out, k = [], 0
    for ch in text:
        if ch == " ":
            out.append(" ")
            continue
        a, b = t0 + k * step, t0 + k * step + 260
        out.append(f"{{\\alpha&HFF&\\blur6{extra_from}\\t({a},{b},\\alpha&H00&\\blur0{extra_to})}}{ch}")
        k += 1
    return "".join(out)


def per_word(text, t0, step):
    """Telugu stays shaped inside each word; words appear one after another."""
    out = []
    for k, w in enumerate(text.split(" ")):
        a, b = t0 + k * step, t0 + k * step + 320
        out.append(f"{{\\alpha&HFF&\\blur8\\t({a},{b},\\alpha&H00&\\blur0)}}{w}")
    return " ".join(out)


def highlight_line(st, en, y, colour, tel, eng):
    """Highlighter bar wipes in, Telugu words rise out of it, English types below."""
    w, h, dy = measure(tel, TEL_FONT, TEL_SIZE)
    bw, bh = w + 64, h + 40
    x0, x1 = 540 - bw / 2, 540 + bw / 2
    y0, y1 = y - bh / 2, y + bh / 2
    d = int((en - st) * 1000)
    # bar: wipe in left->right, wipe out to the right
    ev(0, st, en, "Draw", f"\\an5\\pos(540,{y})\\c{colour}\\clip({x0:.0f},0,{x0:.0f},{H})"
       f"\\t(0,380,0.5,\\clip({x0:.0f},0,{x1:.0f},{H}))\\t({d - 320},{d},2,\\clip({x1:.0f},0,{x1:.0f},{H}))",
       "{\\p1}" + rrect(bw, bh, 18) + "{\\p0}")
    # Telugu: rises from inside the bar, word by word
    ty = y - dy
    ev(1, st, en, "Tel", f"\\an5\\move(540,{ty + bh * 0.8:.0f},540,{ty:.0f},180,620)\\c{DARK}"
       f"\\clip(0,{y0:.0f},{W},{y1:.0f})\\fad(0,260)", per_word(tel, 160, 130))
    if eng:
        ey = y1 + 58
        ev(0, st + 0.45, en, "Eng", f"\\an5\\pos(540,{ey:.0f})\\c&H000000&\\blur6\\bord2\\3c&H000000&"
           f"\\1a&H70&\\3a&H90&\\fad(0,260)", eng)
        ev(1, st + 0.45, en, "Eng", f"\\an5\\pos(540,{ey:.0f})\\c{WHITE}\\fad(0,260)",
           per_letter(eng, 0, 32))


# scenes
scene_t = []
for k, (s0, s1, col, tel, eng) in enumerate(SCENES):
    st = starts[s0] + (0.9 if k == 0 else 0.15)
    en = starts[s1] + SEGS[s1][3] * BEAT + (0.1 if SEGS[s1][4] != "cut" else 0.0)
    if s1 == len(SEGS) - 1:
        en = END + 0.15
    y = 1010 if k == 0 else 1360
    highlight_line(st, en, y, BAR[col], tel, eng)
    scene_t.append((st, en))

# opening title: letters drift together and sharpen
t_st, t_en = 0.35, scene_t[0][1]
ttl = "PARVATESHA FARM"
ev(0, t_st, t_en, "Title", f"\\an5\\pos(540,850)\\c&H000000&\\bord3\\3c&H000000&\\blur10\\1a&H60&\\3a&H90&"
   f"\\fsp34\\t(0,1600,0.5,\\fsp12)\\fad(500,260)", ttl)
ev(1, t_st, t_en, "Title", f"\\an5\\pos(540,850)\\c{WHITE}\\fsp34\\t(0,1600,0.5,\\fsp12)\\fad(0,260)",
   per_letter(ttl, 0, 55))

# end card (dark ink on cream)
c0 = END + 0.25
cd = int((TOTAL - c0) * 1000)
ring_d = CIRC_D + 26
ev(2, c0, TOTAL, "Draw", f"\\an5\\pos({CIRC_CX},{CIRC_CY})\\1a&HFF&\\bord3.5\\3c{GOLD}\\fscx85\\fscy85"
   f"\\t(0,600,0.5,\\fscx100\\fscy100)\\fad(400,0)", "{\\p1}" + circle(ring_d) + "{\\p0}")
ev(2, c0, TOTAL, "Draw", f"\\an7\\pos(40,40)\\c{GOLD}\\1a&HFF&\\bord1.5\\3c{GOLD}\\fad(800,0)",
   "{\\p1}" + rrect(W - 80, H - 80, 24) + "{\\p0}")
ev(2, c0 + 0.2, TOTAL, "Brand", f"\\an5\\pos(540,930)\\c{DARK}\\fsp26\\t(0,1400,0.5,\\fsp9)",
   per_letter("PARVATESHA FARM", 0, 45))
ev(2, c0 + 0.6, TOTAL, "TelEnd", f"\\an5\\move(540,1050,540,1030,0,500)\\c{GOLD}\\fad(450,0)",
   "సంప్రదాయ బిలోనా నెయ్యి")
ev(2, c0 + 0.8, TOTAL, "Draw", f"\\an5\\pos(540,1104)\\c{GOLD}\\fscx0\\t(0,600,0.5,\\fscx100)",
   "{\\p1}m 0 0 l 220 0 l 220 3 l 0 3{\\p0}")
ev(2, c0 + 1.0, TOTAL, "TelS", f"\\an5\\pos(540,1182)\\c{DARK}\\fad(450,0)", "ఆర్డర్ల కోసం సంప్రదించండి")
# phone number types itself out, digit by digit
t_type = int(1.25 * 1000)
ev(2, c0, TOTAL, "Phone", f"\\an5\\pos(540,1275)\\c{DARK}", per_letter(PHONE, t_type, 60))
ev(2, c0 + 1.9, TOTAL, "Eng", f"\\an5\\pos(540,1350)\\c{GOLD}\\fsp10\\fad(400,0)", "CALL  ·  WHATSAPP")
# order button: pops in, then pulses gently
pulse = "".join(f"\\t({1200 + k * 1200},{1800 + k * 1200},\\fscx104\\fscy104)"
                f"\\t({1800 + k * 1200},{2400 + k * 1200},\\fscx100\\fscy100)" for k in range(2))
ev(2, c0 + 2.2, TOTAL, "Draw", f"\\an5\\pos(540,1470)\\c{GREEN}\\fscx60\\fscy60"
   f"\\t(0,320,0.5,\\fscx100\\fscy100){pulse}", "{\\p1}" + rrect(460, 108, 54) + "{\\p0}")
ev(3, c0 + 2.3, TOTAL, "Cta", f"\\an5\\pos(540,1470)\\c{CREAM}\\fad(250,0){pulse}", "ORDER NOW")

STYLES = [  # name, font, size, bold, spacing
    ("Tel", TEL_FONT, TEL_SIZE, 0, 0),
    ("TelEnd", TEL_FONT, 136, 0, 0),
    ("TelS", TEL_FONT, 104, 0, 0),
    ("Eng", "Poppins SemiBold", 40, 0, 6),
    ("Title", "Cinzel SemiBold", 78, 0, 12),
    ("Brand", "Cinzel SemiBold", 76, 0, 9),
    ("Phone", "Poppins SemiBold", 74, 0, 2),
    ("Cta", "Poppins SemiBold", 38, 0, 8),
    ("Draw", "Poppins Medium", 20, 0, 0),
]
ass = os.path.join(WORK, "reel3.ass")
L = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
     "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
     "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
     "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
     "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"]
for n, f, sz, b, spc in STYLES:
    L.append(f"Style: {n},{f},{sz},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,{b},0,0,0,100,100,"
             f"{spc},0,1,0,0,5,0,0,0,1")
L += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"] + EV
with open(ass, "w", encoding="utf-8") as fh:
    fh.write("\n".join(L) + "\n")

# ------------------------------------------------------------ assemble
inp = []
for f in files + [card]:
    inp += ["-i", f]
n = len(files) + 1
inp += ["-i", MUSIC]
fc, prev = [], "[0:v]"
for i in range(1, n):
    _, _, _, _, tr, xf, *_ = SEGS[i - 1]
    tr = "fade" if tr == "cut" else tr
    off = starts[i] if i < len(SEGS) else END
    fc.append(f"{prev}[{i}:v]xfade=transition={tr}:duration={xf:.3f}:offset={off:.3f}[x{i}]")
    prev = f"[x{i}]"
fc.append(f"{prev}ass={ass}:fontsdir={FONTS}:shaping=complex,"
          f"fade=t=in:st=0:d=0.4,fade=t=out:st={TOTAL - 0.5:.3f}:d=0.5,format=yuv420p[vout]")
fc.append(f"[{n}:a]atrim=0:{TOTAL:.3f},afade=t=out:st={TOTAL - 1.5:.3f}:d=1.5,"
          f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(fc),
     "-map", "[vout]", "-map", "[aout]", "-t", f"{TOTAL:.3f}",
     "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-level", "4.2",
     "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart",
     "-c:a", "aac", "-b:a", "256k", "-ar", "48000", OUT])
print(f"done: {OUT} ({TOTAL:.2f}s, end card at {END:.2f}s)")
