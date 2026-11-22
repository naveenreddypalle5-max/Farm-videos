#!/usr/bin/env python3
"""Build the PARVATESHA FARM Bilona ghee reel from the original clips only.

Usage: python3 build_reel.py <clips_dir> <fonts_dir> <work_dir> <output.mp4>

Every frame comes from the uploaded footage. The script only trims, changes
speed, regrades colour, upscales, cross-fades and overlays the Telugu captions.
"""
import glob
import os
import re
import subprocess
import sys

CLIPS, FONTS, WORK, OUT = sys.argv[1:5]
W, H, FPS = 1080, 1920, 30
XF = 0.5  # cross-fade length (s)
os.makedirs(WORK, exist_ok=True)


def clip(prefix):
    return glob.glob(os.path.join(CLIPS, prefix + "*"))[0]


# (clip, in, out, speed, caption-group[, crop-zoom])
# Speed < 1 is slow motion (motion-interpolated).
SEGMENTS = [
    ("c88ad34e", 0.00, 0.90, 0.36, 0),  # milk in the steel vessel
    ("c88ad34e", 1.80, 5.40, 0.90, 1),  # milk flowing from the tap
    ("454f31fc", 0.00, 1.00, 0.33, 2),  # set curd in the churning pot
    ("64f40d6b", 2.00, 4.40, 1.00, 3),  # wooden churner revealed
    ("64f40d6b", 14.00, 16.20, 1.00, 3),  # hands on the churner
    ("64f40d6b", 17.50, 21.00, 1.00, 3),  # bilona churning machine
    ("36c8c524", 1.00, 2.80, 0.80, 4),  # butter rising in the tub
    ("46d75d2b", 0.00, 3.00, 0.75, 4),  # hands gathering butter
    ("187ba50d", 0.00, 2.00, 0.85, 5),  # butter in the pan
    ("ff3939bc", 0.30, 2.50, 1.00, 5),  # butter melting, white froth
    ("5fbfb1c9", 2.00, 4.30, 1.00, 5),  # turning golden, ladle
    ("e2695c1b", 1.00, 3.30, 1.00, 5),  # golden ghee simmering
    ("8e1c51ca", 0.00, 3.40, 0.55, 6, 1.18),  # finished golden ghee, top-down (crop out hand)
]

CAPTIONS = [
    "పాల నుంచి నెయ్యి వరకు...",
    "స్వచ్ఛమైన ఆవు పాలు",
    "పెరుగుగా మార్చి",
    "సంప్రదాయ బిలోనా పద్ధతిలో చిలికి",
    "వెన్నను వేరు చేసి",
    "నెయ్యిగా తయారు చేసి",
    "PARVATESHA FARM",
]

# Warm, earthy, natural grade + gentle vignette.
GRADE = (
    "hqdn3d=1.5:1.5:3:3,"
    f"scale={W}:{H}:flags=lanczos,"
    "unsharp=5:5:0.55:5:5:0.0,"
    "eq=contrast=1.05:brightness=-0.012:saturation=1.06:gamma=0.98,"
    "colorbalance=rs=0.025:gs=0.0:bs=-0.035:rm=0.03:gm=0.008:bm=-0.03:rh=0.015:bh=-0.03,"
    "curves=master='0/0.02 0.25/0.22 0.5/0.5 0.75/0.78 1/0.97',"
    "vignette=angle=PI/5.5"
)


def run(cmd):
    subprocess.run(cmd, check=True)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=framelog=quiet",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else -70.0


seg_files, durs = [], []
for i, (pre, a, b, sp, _, *opt) in enumerate(SEGMENTS):
    src = clip(pre)
    dur = (b - a) / sp
    durs.append(dur)
    vf = f"setpts=(PTS-STARTPTS)/{sp},"
    if sp < 0.98:
        vf += f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
    if opt:  # gentle punch-in, keeping the top-centre of the frame
        z = opt[0]
        vf += f"crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:(ih-ih/{z})*0.25,"
    vf += f"fps={FPS},{GRADE},setsar=1,format=yuv420p"
    # Natural sound: real-time audio from the in-point (never pitch-stretched),
    # trimmed to the segment length; padded if the clip runs out.
    af = (f"atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,highpass=f=70,lowpass=f=14000,"
          f"apad,atrim=0:{dur:.3f},aresample=48000,aformat=channel_layouts=stereo")
    raw = os.path.join(WORK, f"seg{i:02d}_raw.mov")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{b - a + 0.1}", "-i", src,
         "-map", "0:v", "-vf", vf, "-frames:v", str(round(dur * FPS)),
         "-c:v", "libx264", "-crf", "10", "-preset", "medium", "-an", raw + ".v.mp4"])
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-i", src, "-map", "0:a",
         "-af", af, "-c:a", "pcm_s16le", raw + ".a.wav"])
    # Balance each segment's ambience to about -27 LUFS (cap the boost so
    # near-silent clips don't turn into hiss).
    gain = max(-12.0, min(14.0, -27.0 - lufs(raw + ".a.wav")))
    out = os.path.join(WORK, f"seg{i:02d}.mov")
    run(["ffmpeg", "-v", "error", "-y", "-i", raw + ".v.mp4", "-i", raw + ".a.wav",
         "-af", f"volume={gain:.1f}dB", "-c:v", "copy", "-c:a", "pcm_s16le", "-shortest", out])
    seg_files.append(out)
    print(f"seg{i:02d} {pre} {a}-{b} x{sp} -> {dur:.2f}s gain {gain:+.1f}dB", flush=True)

# Segment start times on the final timeline (each cross-fade overlaps by XF).
starts, t = [], 0.0
for d in durs:
    starts.append(t)
    t += d - XF
total = t + XF

# --- cross-fade chain ---
inputs, fc = [], []
for f in seg_files:
    inputs += ["-i", f]
vprev, aprev = "[0:v]", "[0:a]"
for i in range(1, len(seg_files)):
    off = starts[i]
    fc.append(f"{vprev}[{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[v{i}]")
    fc.append(f"{aprev}[{i}:a]acrossfade=d={XF}:c1=tri:c2=tri[a{i}]")
    vprev, aprev = f"[v{i}]", f"[a{i}]"


# --- captions (ASS, rendered by libass with proper Telugu shaping) ---
def ts(x):
    x = max(0.0, x)
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"


groups = {}
for i, s in enumerate(SEGMENTS):
    g = s[4]
    st, en = starts[i], starts[i] + durs[i]
    lo, hi = groups.get(g, (st, en))
    groups[g] = (min(lo, st), max(hi, en))

ass = os.path.join(WORK, "captions.ass")
cream = "&H00D9EAF5"  # BGR of a warm cream (#F5EAD9)
gold = "&H0064B4D9"   # BGR of a soft gold (#D9B464)
lines = [
    "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
    "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
    "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
    "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    f"Style: Cap,Noto Serif Telugu Medium,80,{cream},{cream},&H78000000,&H8C000000,0,0,0,0,"
    "100,100,0,0,1,3.2,1.5,2,80,80,540,1",
    f"Style: Brand,Cormorant Garamond SemiBold,92,{cream},{cream},&H50000000,&H96000000,0,0,0,0,"
    "100,100,14,0,1,0.4,2.4,5,60,60,0,1",
    f"Style: Rule,Cormorant Garamond SemiBold,40,{gold},{gold},&H00000000,&H96000000,0,0,0,0,"
    "100,100,0,0,1,0,1.5,5,60,60,0,1",
    "", "[Events]",
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
]
for g, text in enumerate(CAPTIONS):
    lo, hi = groups[g]
    if text == "PARVATESHA FARM":
        st, en = lo + 0.9, total
        lines.append(f"Dialogue: 1,{ts(st)},{ts(en)},Brand,,0,0,0,,"
                     f"{{\\fad(900,0)\\blur2\\pos({W // 2},{H // 2 - 20})}}{text}")
        lines.append(f"Dialogue: 1,{ts(st + 0.3)},{ts(en)},Rule,,0,0,0,,"
                     f"{{\\fad(900,0)\\pos({W // 2},{H // 2 + 62})}}———  ✦  ———")
    else:
        # Caption sits inside its section, clear of the cross-fades.
        st = lo + (0.35 if g else 0.5)
        en = hi - XF - 0.1
        lines.append(f"Dialogue: 0,{ts(st)},{ts(en)},Cap,,0,0,0,,{{\\fad(450,400)\\blur5}}{text}")
with open(ass, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

# End: darken slightly under the brand name and fade to black.
brand_start = groups[6][0] + 0.6
fade_out = total - 1.2
fc.append(f"{vprev}eq=brightness=0:enable='gte(t,{brand_start:.2f})',"
          f"curves=master='0/0 1/0.80':enable='gte(t,{brand_start:.2f})',"
          f"ass={ass}:fontsdir={FONTS}:shaping=complex,"
          f"fade=t=in:st=0:d=0.6,fade=t=out:st={fade_out:.2f}:d=1.2,format=yuv420p[vout]")
fc.append(f"{aprev}afade=t=in:st=0:d=0.5,afade=t=out:st={total - 1.6:.2f}:d=1.6,"
          "loudnorm=I=-20:TP=-2:LRA=9,aresample=48000[aout]")

run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
     "-map", "[vout]", "-map", "[aout]",
     "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high", "-level", "4.2",
     "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart",
     "-c:a", "aac", "-b:a", "192k", "-ar", "48000", OUT])
print(f"done: {OUT} ({total:.2f}s)")
