#!/usr/bin/env python3
"""Reel 5: a 10-second cinematic bumper of the best butter and ghee shots.

Usage:
  python3 build_reel_5_bumper.py <clips_dir> <fonts_dir> <work_dir> <music.wav> <output.mp4>

Only the uploaded footage is used. 24 fps, warm cinematic grade with bloom and
grain, cuts on the 96 BPM grid of make_music_5.py: five hero shots in 6.25 s,
then a brand and contact end card over the finished ghee.
"""
import glob
import os
import subprocess
import sys

CLIPS, FONTS, WORK, MUSIC, OUT = sys.argv[1:6]
W, H, FPS = 1080, 1920, 24
BEAT = 60.0 / 96.0
CUT = 2 / FPS
os.makedirs(WORK, exist_ok=True)
PHONE = "+91 93905 07506"
CREAM, GOLD, DARK = "&HE2F4FF&", "&H4FB8E8&", "&H0E1A26&"


def clip(prefix):
    return glob.glob(os.path.join(CLIPS, prefix + "*"))[0]


def run(cmd):
    subprocess.run(cmd, check=True)


# (clip, in, available-until, beats, transition-out, xf, speed, zoom, crop-zoom, crop anchor)
SEGS = [
    ("46d75d2b", 0.0, 3.0, 2, "zoomin", 0.25, 0.5, 1.10, 1.0, 0.15),     # hands holding fresh butter
    ("187ba50d", 2.7, 5.3, 2, "fade", CUT, 0.6, 1.08, 1.0, 0.5),         # butter over the flame
    ("ff3939bc", 0.3, 2.5, 2, "fadewhite", 0.30, 0.6, 1.08, 1.0, 0.5),   # melting into white froth
    ("5fbfb1c9", 2.0, 4.5, 2, "fade", CUT, 0.6, 1.08, 1.0, 0.5),         # golden ghee, ladle
    ("e2695c1b", 1.0, 3.4, 2, "zoomin", 0.30, 0.6, 1.08, 1.0, 0.5),      # golden ghee bubbling
    ("8e1c51ca", 0.0, 3.4, 6, None, 0.0, 0.6, 1.14, 1.18, 0.5),          # the finished ghee (end card)
]

GRADE = ("unsharp=5:5:0.5:5:5:0.0,"
         "eq=contrast=1.08:brightness=-0.01:saturation=1.12:gamma=0.97,"
         "colorbalance=rs=0.03:bs=-0.045:rm=0.04:gm=0.01:bm=-0.04:rh=0.025:bh=-0.04,"
         "curves=master='0/0.02 0.25/0.21 0.5/0.5 0.75/0.8 1/0.97',"
         "vignette=angle=PI/4.8")


def render(src, a, avail, dur, out, sp, zoom, cz, cy):
    sp = min(sp, (avail - a) / dur)
    vf = f"setpts=(PTS-STARTPTS)/{sp:.4f},"
    if sp < 0.97:
        vf += f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
    vf += f"fps={FPS},hqdn3d=1.5:1.5:3:3,"
    if cz > 1.0:
        vf += f"crop=iw/{cz}:ih/{cz}:(iw-iw/{cz})/2:(ih-ih/{cz})*0.25,"
    vf += (f"scale=w='2*trunc({W // 2}*(1+{zoom - 1:.3f}*t/{dur:.3f}))':h=-2:eval=frame:flags=lanczos,"
           f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{cy},{GRADE},setsar=1,format=yuv420p")
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
TOTAL = starts[-1] + durs[-1]
END = starts[-1]


def ts(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def rrect(w, h, r):
    k = r * 0.45
    return (f"m {r} 0 l {w - r} 0 b {w - k} 0 {w} {k} {w} {r} l {w} {h - r} "
            f"b {w} {h - k} {w - k} {h} {w - r} {h} l {r} {h} b {k} {h} 0 {h - k} 0 {h - r} "
            f"l 0 {r} b 0 {k} {k} 0 {r} 0")


EV = []


def ev(layer, st, en, style, tags, text, shadow=True):
    if shadow:
        base = tags.split("\\c&H")[0]
        EV.append(f"Dialogue: {layer},{ts(st)},{ts(en)},{style},,0,0,0,,"
                  f"{{{base}\\c&H000000&\\3c&H000000&\\bord7\\blur16\\1a&H30&\\3a&H58&}}{text}")
    EV.append(f"Dialogue: {layer + 1},{ts(st)},{ts(en)},{style},,0,0,0,,{{{tags}}}{text}")


def slam(st, en, y, word, colour, size_style):
    """Big word lands with a scale/blur impact, then drifts slowly forward."""
    d = int((en - st) * 1000)
    ev(2, st, en, size_style, f"\\an5\\pos(540,{y})\\fscx135\\fscy135\\blur14\\alpha&HFF&"
       f"\\t(0,260,0.4,\\fscx100\\fscy100\\blur0\\alpha&H00&)\\t(260,{d - 250},\\fscx106\\fscy106)"
       f"\\t({d - 250},{d},\\blur10\\alpha&HFF&)\\c{colour}", word)


# brand presence through the cuts
ev(2, 0.3, END + 0.1, "Small", f"\\an5\\pos(540,300)\\fad(400,200)\\fsp14\\c{CREAM}", "PARVATESHA FARM")
# butter / ghee impacts
b_en, g_st = starts[2] - 0.05, starts[2] + 0.12
slam(0.12, b_en, 830, "వెన్న", CREAM, "Big")
ev(2, 0.45, b_en, "Label", f"\\an5\\pos(540,1030)\\fad(250,200)\\fsp6\\t(0,1800,\\fsp12)\\c{CREAM}",
   "FRESH WHITE BUTTER")
slam(g_st, END + 0.05, 830, "నెయ్యి", GOLD, "Big")
ev(2, g_st + 0.3, END + 0.05, "Label", f"\\an5\\pos(540,1030)\\fad(250,200)\\fsp6\\t(0,3200,\\fsp12)\\c{CREAM}",
   "GOLDEN BILONA GHEE")

# end card: darken the hero shot, then brand + contact
c0 = END
box = "{\\p1}" + f"m 0 0 l {W} 0 l {W} {H} l 0 {H}" + "{\\p0}"
ev(0, c0, TOTAL, "Draw", f"\\an7\\pos(0,0)\\c&H000000&\\alpha&HFF&\\t(0,500,\\alpha&H5A&)", box, False)
ev(2, c0 + 0.1, TOTAL, "Brand", f"\\an5\\pos(540,740)\\fscx120\\fscy120\\blur10\\alpha&HFF&"
   f"\\t(0,300,0.4,\\fscx100\\fscy100\\blur0\\alpha&H00&)\\fsp6\\t(300,3600,\\fsp10)\\c{GOLD}", "PARVATESHA FARM")
ev(2, c0 + 0.35, TOTAL, "TelEnd", f"\\an5\\move(540,866,540,848,0,400)\\fad(350,0)\\c{CREAM}",
   "సంప్రదాయ బిలోనా నెయ్యి")
ev(2, c0 + 0.5, TOTAL, "Draw", f"\\an5\\pos(540,930)\\fscx0\\t(0,500,0.5,\\fscx100)\\c{GOLD}",
   "{\\p1}m 0 0 l 300 0 l 300 3 l 0 3{\\p0}", False)
ev(2, c0 + 0.7, TOTAL, "Phone", f"\\an5\\move(540,1070,540,1050,0,400)\\fad(350,0)\\c{CREAM}", PHONE)
ev(2, c0 + 0.9, TOTAL, "Label", f"\\an5\\pos(540,1128)\\fad(350,0)\\fsp10\\c{GOLD}", "CALL  ·  WHATSAPP")
ev(2, c0 + 1.1, TOTAL, "Draw", f"\\an5\\pos(540,1250)\\fscx60\\fscy60\\t(0,300,0.5,\\fscx100\\fscy100)\\c{GOLD}",
   "{\\p1}" + rrect(440, 100, 50) + "{\\p0}", False)
ev(4, c0 + 1.2, TOTAL, "Cta", f"\\an5\\pos(540,1250)\\fad(200,0)\\fsp8\\c{DARK}", "ORDER NOW", False)

STYLES = [  # name, font, size, spacing
    ("Big", "Sree Krushnadevaraya", 450, 0),
    ("TelEnd", "Ramaraja", 122, 0),
    ("Small", "Cinzel SemiBold", 36, 14),
    ("Label", "Cinzel SemiBold", 42, 6),
    ("Brand", "Cinzel SemiBold", 84, 6),
    ("Phone", "Poppins SemiBold", 74, 2),
    ("Cta", "Poppins SemiBold", 38, 8),
    ("Draw", "Poppins SemiBold", 20, 0),
]
ass = os.path.join(WORK, "reel5.ass")
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
fc.append(f"{prev}format=gbrp,split[p0][p1];[p1]gblur=sigma=26[pb];"
          f"[p0][pb]blend=all_mode=screen:all_opacity=0.16,format=yuv420p,noise=c0s=6:c0f=t+u,"
          f"ass={ass}:fontsdir={FONTS}:shaping=complex,"
          f"fade=t=in:st=0:d=0.25,fade=t=out:st={TOTAL - 0.4:.3f}:d=0.4,format=yuv420p[vout]")
fc.append(f"[{n}:a]atrim=0:{TOTAL:.3f},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(fc),
     "-map", "[vout]", "-map", "[aout]", "-t", f"{TOTAL:.3f}",
     "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-tune", "grain", "-profile:v", "high",
     "-level", "4.2", "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart",
     "-c:a", "aac", "-b:a", "256k", "-ar", "48000", OUT])
print(f"done: {OUT} ({TOTAL:.2f}s, end card at {END:.2f}s)")
