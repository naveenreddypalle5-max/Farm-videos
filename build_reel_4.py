#!/usr/bin/env python3
"""Reel 4 for PARVATESHA FARM: a short-film style reel with organic music.

Usage:
  python3 build_reel_4.py <clips_dir> <fonts_dir> <work_dir> <music.wav> <output.mp4>

Every frame of footage comes from the uploaded clips. Cinema treatment: 24 fps,
a 4:5 picture inside black letterbox bars, film-stock grade (soft blacks, warm
highlights, cool shadows), red halation around highlights, film grain, opening
credits, roman-numeral chapters, subtitle-style Telugu captions, and an end
card where the bars close in around the ghee to frame the contact details.
Cuts follow the 72 BPM music from make_music_4.py.
"""
import glob
import os
import subprocess
import sys

CLIPS, FONTS, WORK, MUSIC, OUT = sys.argv[1:6]
W, H, FPS = 1080, 1920, 24
PW, PH = 1080, 1350           # picture area (4:5)
BAR = (H - PH) // 2           # 285 px letterbox bars
BEAT = 60.0 / 72.0
CUT = 2 / FPS
DIS = 0.8                     # slow cinematic dissolve
os.makedirs(WORK, exist_ok=True)
PHONE = "+91 93905 07506"


def clip(prefix):
    return glob.glob(os.path.join(CLIPS, prefix + "*"))[0]


def run(cmd):
    subprocess.run(cmd, check=True)


# (clip, in, available-until, beats, transition-out, xf, max speed, zoom, crop-zoom, crop anchor)
SEGS = [
    ("64f40d6b", 20.0, 24.4, 5, "fade", DIS, 0.6, 1.06, 1.0, 0.45),   # 0 establishing: the churning room
    ("c88ad34e", 0.0, 1.0, 2, "fade", CUT, 1.0, 1.06, 1.0, 0.40),     # 1 milk in the vessel
    ("c88ad34e", 1.8, 5.8, 4, "fade", DIS, 0.5, 1.04, 1.0, 0.45),     # 2 milk from the tap
    ("454f31fc", 0.0, 1.0, 4, "fade", DIS, 1.0, 1.08, 1.0, 0.30),     # 3 curd
    ("64f40d6b", 12.0, 15.0, 3, "fade", CUT, 0.6, 1.04, 1.0, 0.40),   # 4 man at the churner
    ("64f40d6b", 0.0, 2.6, 2, "fade", CUT, 0.6, 1.04, 1.0, 0.40),     # 5 churner revealed
    ("454f31fc", 1.5, 4.3, 2, "fade", DIS, 0.6, 1.04, 1.0, 0.40),     # 6 hand on the lid
    ("46d75d2b", 0.0, 3.0, 3, "fade", CUT, 0.5, 1.05, 1.0, 0.25),     # 7 butter in her hands
    ("36c8c524", 0.0, 2.8, 2, "fade", DIS, 0.6, 1.04, 1.0, 0.55),     # 8 butter in the tub
    ("187ba50d", 2.7, 5.3, 3, "fade", CUT, 0.6, 1.05, 1.0, 0.30),     # 9 butter over the flame
    ("5fbfb1c9", 5.0, 9.0, 2, "fade", CUT, 0.6, 1.05, 1.0, 0.45),     # 10 stirring golden ghee
    ("8e1c51ca", 0.0, 3.4, 2, "fade", DIS, 0.6, 1.08, 1.18, 0.30),    # 11 the finished ghee
    ("8e1c51ca", 0.8, 3.4, 7, None, 0.0, 0.4, 1.10, 1.18, 0.30),      # 12 end-card background
]
CHAPTERS = [  # (first seg, numeral, English, Telugu subtitle)
    (1, "I", "MILK", "స్వచ్ఛమైన ఆవు పాలు"),
    (3, "II", "CURD", "పెరుగుగా మార్చి"),
    (4, "III", "CHURNING", "సంప్రదాయ బిలోనా పద్ధతిలో చిలికి"),
    (7, "IV", "BUTTER", "వెన్నను వేరు చేసి"),
    (9, "V", "GHEE", "నెయ్యిగా తయారు చేసి"),
]

PRE = "hqdn3d=1.5:1.5:3:3"
# Film-stock look: lifted blacks, rolled-off highlights, warm highs, cool lows.
FILM = ("curves=r='0/0.055 0.25/0.26 0.5/0.53 0.75/0.79 1/0.955'"
        ":g='0/0.05 0.25/0.24 0.5/0.5 0.75/0.76 1/0.94'"
        ":b='0/0.075 0.25/0.25 0.5/0.47 0.75/0.71 1/0.88',"
        "eq=contrast=1.06:saturation=0.9,"
        "colorbalance=rs=-0.03:bs=0.025:rh=0.035:bh=-0.035,"
        "unsharp=5:5:0.4:5:5:0.0")


def render(src, a, avail, dur, out, sp, zoom, cz, cy):
    sp = min(sp, (avail - a) / dur)
    vf = f"setpts=(PTS-STARTPTS)/{sp:.4f},"
    if sp < 0.97:
        vf += f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
    vf += f"fps={FPS},{PRE},"
    if cz > 1.0:
        vf += f"crop=iw/{cz}:ih/{cz}:(iw-iw/{cz})/2:(ih-ih/{cz})*0.25,"
    vf += (f"scale=w='2*trunc({PW // 2}*(1+{zoom - 1:.3f}*t/{dur:.3f}))':h=-2:eval=frame:flags=lanczos,"
           f"crop={PW}:{PH}:(iw-{PW})/2:(ih-{PH})*{cy},{FILM},setsar=1,format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{avail - a + 0.1}", "-i", src,
         "-an", "-vf", vf, "-frames:v", str(round(dur * FPS)),
         "-c:v", "libx264", "-crf", "10", "-preset", "medium", out])


starts, durs, files = [], [], []
t = 0.0
for i, (pre, a, avail, beats, tr, xf, sp, zoom, cz, cy) in enumerate(SEGS):
    dur = beats * BEAT + xf
    starts.append(t)
    durs.append(dur)
    t += beats * BEAT
    out = os.path.join(WORK, f"s{i:02d}.mp4")
    if not (os.path.exists(out) and not os.environ.get("REBUILD")):
        render(clip(pre), a, avail, dur, out, sp, zoom, cz, cy)
    files.append(out)
    print(f"s{i:02d} {pre} -> {dur:.2f}s @ {starts[-1]:.2f}s", flush=True)
TOTAL = starts[-1] + durs[-1]
END = starts[-1]


# ------------------------------------------------------------ titles (ASS)
def ts(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def rrect(w, h, r):
    k = r * 0.45
    return (f"m {r} 0 l {w - r} 0 b {w - k} 0 {w} {k} {w} {r} l {w} {h - r} "
            f"b {w} {h - k} {w - k} {h} {w - r} {h} l {r} {h} b {k} {h} 0 {h - k} 0 {h - r} "
            f"l 0 {r} b 0 {k} {k} 0 {r} 0")


EV = []


def ev(layer, st, en, style, tags, text, shadow=False):
    if shadow:
        EV.append(f"Dialogue: {layer},{ts(st)},{ts(en)},{style},,0,0,0,,"
                  f"{{{tags}\\c&H000000&\\3c&H000000&\\bord3\\blur9\\1a&H40&\\3a&H80&}}{text}")
    EV.append(f"Dialogue: {layer + 1},{ts(st)},{ts(en)},{style},,0,0,0,,{{{tags}}}{text}")


WARM = "&HE8F2F8&"   # warm white
DIM = "&HB4C8D6&"    # muted parchment
GOLD = "&H5FB4E0&"   # soft gold

# letterbox: static bars, then they close in for the end card
close_ms, close_dur = int((END + 0.2) * 1000), 1400
top_to, bot_to = 600, 1240
box = "{\\p1}" + f"m 0 0 l {W} 0 l {W} {H} l 0 {H}" + "{\\p0}"
ev(5, 0, TOTAL, "Draw", f"\\an7\\pos(0,0)\\c&H000000&\\clip(0,0,{W},{BAR})"
   f"\\t({close_ms},{close_ms + close_dur},0.6,\\clip(0,0,{W},{top_to}))", box)
ev(5, 0, TOTAL, "Draw", f"\\an7\\pos(0,0)\\c&H000000&\\clip(0,{H - BAR},{W},{H})"
   f"\\t({close_ms},{close_ms + close_dur},0.6,\\clip(0,{bot_to},{W},{H}))", box)

# opening credits over the establishing shot
o_en = starts[1] + 0.2
ev(7, 0.9, o_en, "Credit", f"\\an5\\pos(540,880)\\c{WARM}\\fad(1200,600)\\blur3\\t(0,1200,\\blur0)"
   f"\\fsp10\\t(0,{int((o_en - 0.9) * 1000)},\\fsp16)", "PARVATESHA FARM", True)
ev(7, 1.7, o_en, "Small", f"\\an5\\pos(540,985)\\c{DIM}\\fad(1000,600)\\fsp10", "A SHORT FILM ON BILONA GHEE", True)
ev(7, 2.3, o_en, "TelSub", f"\\an5\\pos(540,1085)\\c{WARM}\\fad(900,600)", "పాల నుంచి నెయ్యి వరకు...", True)

# chapters: numeral in the top bar, subtitle near the bottom of the picture
for k, (si, num, eng, tel) in enumerate(CHAPTERS):
    st = starts[si] + 0.25
    nxt = CHAPTERS[k + 1][0] if k + 1 < len(CHAPTERS) else len(SEGS) - 1
    en = starts[nxt] + (0.4 if nxt != len(SEGS) - 1 else 0.3)
    ev(7, st, en, "Chapter", f"\\an5\\pos(540,212)\\c{GOLD}\\fad(700,500)\\fsp14", f"{num}  ·  {eng}")
    ev(7, st + 0.35, en, "TelSub", f"\\an5\\pos(540,{BAR + PH - 130})\\c{WARM}\\fad(700,500)"
       f"\\blur4\\t(0,600,\\blur0.4)", tel, True)

# end card: in the black space the bars open up
c0 = END + 1.1
ev(7, c0, TOTAL, "Brand", f"\\an5\\pos(540,395)\\c{WARM}\\fad(1100,0)\\fsp14\\t(0,2500,0.6,\\fsp20)",
   "PARVATESHA FARM")
ev(7, c0 + 0.5, TOTAL, "TelEnd", f"\\an5\\pos(540,500)\\c{GOLD}\\fad(900,0)", "సంప్రదాయ బిలోనా నెయ్యి")
ev(7, c0 + 0.9, TOTAL, "Draw", f"\\an5\\pos(540,1300)\\c{GOLD}\\fscx0\\t(0,800,0.5,\\fscx100)",
   "{\\p1}m 0 0 l 180 0 l 180 2 l 0 2{\\p0}")
ev(7, c0 + 1.0, TOTAL, "TelS", f"\\an5\\pos(540,1365)\\c{DIM}\\fad(800,0)", "ఆర్డర్ల కోసం సంప్రదించండి")
ev(7, c0 + 1.3, TOTAL, "Phone", f"\\an5\\pos(540,1450)\\c{WARM}\\fad(900,0)\\fsp4", PHONE)
ev(7, c0 + 1.6, TOTAL, "Small", f"\\an5\\pos(540,1522)\\c{GOLD}\\fad(800,0)\\fsp12", "CALL  ·  WHATSAPP")
ev(7, c0 + 2.0, TOTAL, "Draw", f"\\an5\\pos(540,1610)\\1a&HFF&\\bord1.6\\3c{WARM}\\fad(700,0)",
   "{\\p1}" + rrect(380, 84, 42) + "{\\p0}")
ev(7, c0 + 2.1, TOTAL, "Small", f"\\an5\\pos(540,1610)\\c{WARM}\\fad(700,0)\\fsp12", "ORDER NOW")

STYLES = [  # name, font, size, spacing
    ("Credit", "Cormorant Garamond SemiBold", 80, 10),
    ("Small", "Cormorant Garamond SemiBold", 38, 10),
    ("Chapter", "Cormorant Garamond SemiBold", 46, 14),
    ("TelSub", "Mandali", 100, 0),
    ("TelEnd", "Mandali", 92, 0),
    ("TelS", "Mandali", 72, 0),
    ("Brand", "Cormorant Garamond SemiBold", 70, 14),
    ("Phone", "Cormorant Garamond SemiBold", 76, 4),
    ("Draw", "Cormorant Garamond SemiBold", 20, 0),
]
ass = os.path.join(WORK, "reel4.ass")
L = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
     "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
     "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
     "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
     "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"]
for n, f, sz, spc in STYLES:
    L.append(f"Style: {n},{f},{sz},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,"
             f"{spc},0,1,0,0,5,0,0,0,1")
L += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"] + EV
with open(ass, "w", encoding="utf-8") as fh:
    fh.write("\n".join(L) + "\n")

# ------------------------------------------------------------ assemble
inp = []
for f in files:
    inp += ["-i", f]
n = len(files)
inp += ["-i", MUSIC]
fc, prev = [], "[0:v]"
for i in range(1, n):
    tr, xf = SEGS[i - 1][4], SEGS[i - 1][5]
    fc.append(f"{prev}[{i}:v]xfade=transition={tr}:duration={xf:.3f}:offset={starts[i]:.3f}[x{i}]")
    prev = f"[x{i}]"
# halation (warm glow bleeding from highlights) + film grain, then letterbox canvas
fc.append(f"{prev}format=gbrp,split[p0][p1];"
          f"[p1]curves=all='0/0 0.72/0 1/1',gblur=sigma=16,"
          f"colorchannelmixer=rr=1:gg=0.38:bb=0.12[hal];"
          f"[p0][hal]blend=all_mode=screen:all_opacity=0.32,format=yuv420p,"
          f"noise=c0s=9:c0f=t+u,vignette=angle=PI/4.6,"
          f"pad={W}:{H}:0:{BAR}:black,"
          f"ass={ass}:fontsdir={FONTS}:shaping=complex,"
          f"fade=t=in:st=0:d=1.6,fade=t=out:st={TOTAL - 0.8:.3f}:d=0.8,format=yuv420p[vout]")
fc.append(f"[{n}:a]atrim=0:{TOTAL:.3f},afade=t=out:st={TOTAL - 1.8:.3f}:d=1.8,"
          f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(fc),
     "-map", "[vout]", "-map", "[aout]", "-t", f"{TOTAL:.3f}",
     "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-tune", "grain", "-maxrate", "18M", "-bufsize", "36M",
     "-profile:v", "high", "-level", "4.2",
     "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart",
     "-c:a", "aac", "-b:a", "256k", "-ar", "48000", OUT])
print(f"done: {OUT} ({TOTAL:.2f}s, end card at {END:.2f}s)")
