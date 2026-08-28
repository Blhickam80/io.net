#!/usr/bin/env python3
"""
Generate a vertical (Shorts/Reels/TikTok) video by driving a real browser
through the missed-call calculator with a given set of inputs, then
burning in a hook caption (start) and a CTA caption (end) with ffmpeg.

This produces a genuine screen recording (not a mockup) of the actual
live tool with real computed numbers, so whatever a caption/voiceover
claims is guaranteed to match what viewers see on screen.

Requires: pip install playwright  (browsers are already bundled in this
environment at /opt/pw-browsers - do NOT run `playwright install`)
Requires: a full ffmpeg on PATH (the Playwright-bundled one at
/opt/pw-browsers/ffmpeg-* is a stripped build with no drawtext/libx264/
mp4 support - install a real one, e.g. `apt-get install ffmpeg`, first).

Usage:
    python3 automation/record_calculator_short.py \\
        --calls 150 --missed 20 --close 25 --ticket 350 --recall 70 \\
        --hook "You are losing money right now" \\
        --cta "Free calculator - link in description" \\
        --out /path/to/output.mp4

The site must be served locally first, e.g.:
    cd website/public && python3 -m http.server 8123 &
"""
import argparse
import glob
import os
import shutil
import subprocess
import tempfile

from playwright.sync_api import sync_playwright

CHROMIUM_CANDIDATES = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
]


def find_chromium():
    for path in CHROMIUM_CANDIDATES:
        if os.path.exists(path):
            return path
    matches = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
    if matches:
        return matches[0]
    raise SystemExit("Could not locate bundled Chromium binary under /opt/pw-browsers")


def record(base_url, inputs, video_dir):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=find_chromium(), headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            record_video_dir=video_dir,
            record_video_size={"width": 390, "height": 844},
        )
        page = context.new_page()
        page.goto(f"{base_url}/tools/missed-call-calculator.html")
        page.wait_for_timeout(1500)

        field_map = {
            "callsPerMonth": inputs["calls"],
            "missedPct": inputs["missed"],
            "closeRate": inputs["close"],
            "avgTicket": inputs["ticket"],
            "recallPct": inputs["recall"],
        }
        for field_id, value in field_map.items():
            sel = f"#{field_id}"
            page.click(sel)
            page.fill(sel, "")
            page.type(sel, str(value), delay=90)
            page.wait_for_timeout(400)

        page.wait_for_timeout(600)
        page.click("text=Calculate my lost revenue")
        page.wait_for_timeout(600)
        page.eval_on_selector(
            "#resultsCard",
            "el => el.scrollIntoView({behavior: 'smooth', block: 'center'})",
        )
        page.wait_for_timeout(3500)

        context.close()
        browser.close()

    raw = glob.glob(os.path.join(video_dir, "*.webm"))
    if not raw:
        raise SystemExit("Playwright did not produce a video file")
    return raw[0]


def render_final(raw_path, out_path, hook_text, cta_text, hook_window, cta_window):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found on PATH - install a full ffmpeg build first")
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    def esc(text):
        return text.replace("'", "’").replace(":", "\\:")

    vf = (
        "scale=1080:2334,"
        f"drawtext=fontfile={font}:text='{esc(hook_text)}':fontcolor=white:fontsize=56:"
        f"box=1:boxcolor=black@0.55:boxborderw=22:x=(w-text_w)/2:y=140:"
        f"enable='between(t,{hook_window[0]},{hook_window[1]})',"
        f"drawtext=fontfile={font}:text='{esc(cta_text)}':fontcolor=white:fontsize=46:"
        f"box=1:boxcolor=black@0.6:boxborderw=20:x=(w-text_w)/2:y=h-300:"
        f"enable='between(t,{cta_window[0]},{cta_window[1]})'"
    )
    subprocess.run(
        [ffmpeg, "-y", "-i", raw_path, "-vf", vf,
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         "-r", "30", out_path],
        check=True,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8123")
    ap.add_argument("--calls", type=int, required=True)
    ap.add_argument("--missed", type=int, required=True)
    ap.add_argument("--close", type=int, required=True)
    ap.add_argument("--ticket", type=int, required=True)
    ap.add_argument("--recall", type=int, required=True)
    ap.add_argument("--hook", required=True)
    ap.add_argument("--cta", required=True)
    ap.add_argument("--hook-window", nargs=2, type=float, default=[0, 3.2])
    ap.add_argument("--cta-window", nargs=2, type=float, default=[5.3, 9.9])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as video_dir:
        raw = record(
            args.base_url,
            {"calls": args.calls, "missed": args.missed, "close": args.close,
             "ticket": args.ticket, "recall": args.recall},
            video_dir,
        )
        render_final(raw, args.out, args.hook, args.cta, args.hook_window, args.cta_window)

    print(f"Rendered: {args.out}")


if __name__ == "__main__":
    main()
