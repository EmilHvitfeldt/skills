#!/usr/bin/env python3
"""Capture a revealjs deck (or any web page) as a sharp, constant-frame-rate MP4.

Why not Playwright's record_video? It writes a low-bitrate VP8 stream, and re-encoding that
cannot restore detail. This script instead grabs Chrome screencast frames as high-quality JPEGs,
resamples them to a constant frame rate, and encodes with ffmpeg.

Modes
  loop     The deck must auto-advance and loop (auto-slide + loop: true). The first pass is
           discarded (it covers loading iframes/images), and the second pass, from one wrap back
           to slide 1 to the next, becomes the video. The result loops seamlessly.
  seconds  Record N seconds after load (use --seconds). Pair with --warmup to skip loading time.

Examples
  capture_loop.py http://localhost:5266/index.html out.mp4
  capture_loop.py http://localhost:8000/index.html out.mp4 --mode seconds --seconds 20 --warmup 8

Requires: python3 with playwright (and a Chromium build installed), and ffmpeg on PATH.
"""
import argparse
import base64
import bisect
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("output", help="output .mp4 path")
    ap.add_argument("--mode", choices=["loop", "seconds"], default="loop")
    ap.add_argument("--seconds", type=float, default=20, help="duration for --mode seconds")
    ap.add_argument("--warmup", type=float, default=0, help="seconds to wait after load before recording (seconds mode)")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--scale", type=float, default=2, help="device scale factor (2 renders crisper text and canvases)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--quality", type=int, default=95, help="screencast JPEG quality")
    ap.add_argument("--crf", type=int, default=14, help="x264 quality, lower is better")
    ap.add_argument("--timeout", type=float, default=300, help="give up waiting for loops after this many seconds")
    ap.add_argument("--keep-frames", action="store_true", help="keep the temp frame directory and print its path")
    return ap.parse_args()


def capture(args, frames_dir):
    """Return (frames, slide_log) where frames is [(timestamp, path)] and slide_log [(epoch_s, indexh)]."""
    frames = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=args.scale,
        )
        page = ctx.new_page()
        client = ctx.new_cdp_session(page)

        def on_frame(params):
            path = frames_dir / f"f{len(frames):06d}.jpg"
            path.write_bytes(base64.b64decode(params["data"]))
            frames.append((params["metadata"]["timestamp"], str(path)))
            client.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})

        client.on("Page.screencastFrame", on_frame)

        page.goto(args.url, wait_until="load")
        page.wait_for_function("window.Reveal && Reveal.isReady()")
        page.evaluate(
            """() => {
                window.__log = [[Date.now(), Reveal.getIndices().h]];
                Reveal.on('slidechanged', e => window.__log.push([Date.now(), e.indexh]));
            }"""
        )
        client.send(
            "Page.startScreencast",
            {
                "format": "jpeg",
                "quality": args.quality,
                "maxWidth": int(args.width * args.scale),
                "maxHeight": int(args.height * args.scale),
                "everyNthFrame": 1,
            },
        )

        t0 = time.time()
        while True:
            page.wait_for_timeout(500)  # also lets screencast events dispatch
            log = page.evaluate("window.__log")
            if args.mode == "seconds":
                if time.time() - t0 >= args.warmup + args.seconds:
                    break
            else:
                wraps = [i for i, (_, idx) in enumerate(log) if idx == 0 and i > 0]
                if len(wraps) >= 2:
                    break
            if time.time() - t0 > args.timeout + (args.warmup if args.mode == "seconds" else 0):
                sys.exit("Timed out. In loop mode the deck needs auto-slide and loop: true.")
        record_end = time.time()
        client.send("Page.stopScreencast")
        page.wait_for_timeout(300)
        log = page.evaluate("window.__log")
        browser.close()

    slide_log = [(ms / 1000, idx) for ms, idx in log]
    if args.mode == "loop":
        wraps = [i for i, (_, idx) in enumerate(slide_log) if idx == 0 and i > 0]
        start, end = slide_log[wraps[0]][0], slide_log[wraps[1]][0]
    else:
        end = record_end
        start = end - args.seconds
    return frames, start, end


def resample(frames, start, end, fps, out_dir):
    """Pick the latest captured frame at or before each output tick (screencasts are variable rate)."""
    times = [t for t, _ in frames]
    paths = [p for _, p in frames]
    n = round((end - start) * fps)
    for k in range(n):
        i = max(bisect.bisect_right(times, start + k / fps) - 1, 0)
        os.symlink(paths[i], out_dir / f"s{k:06d}.jpg")
    return n


def main():
    args = parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")
    work = Path(tempfile.mkdtemp(prefix="capture_loop_"))
    frames_dir, cfr_dir = work / "frames", work / "cfr"
    frames_dir.mkdir()
    cfr_dir.mkdir()
    try:
        frames, start, end = capture(args, frames_dir)
        if not frames:
            sys.exit("No screencast frames were captured")
        n = resample(frames, start, end, args.fps, cfr_dir)
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-framerate", str(args.fps), "-i", str(cfr_dir / "s%06d.jpg"),
                "-vf", f"scale={args.width}:{args.height}:flags=lanczos,format=yuv420p",
                "-c:v", "libx264", "-crf", str(args.crf), "-preset", "slow",
                "-movflags", "+faststart", "-an", str(out),
            ],
            check=True,
        )
        print(json.dumps({"output": str(out), "frames": n, "seconds": round(n / args.fps, 2), "captured_frames": len(frames)}))
    finally:
        if args.keep_frames:
            print(f"frames kept in {work}", file=sys.stderr)
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
