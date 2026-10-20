---
name: quarto-revealjs-showcase
description: Build a Quarto revealjs deck whose job is to show something off (a website, web app, widget, set of visuals or screenshots) with motion, and optionally capture it as a sharp MP4. Covers full-bleed iframe or image slide backgrounds, caption overlays, auto-advancing looping decks, hiding all presentation chrome, per-slide transitions and speed, auto-animate, and a tested headless capture script that records one clean loop at 1080p. Use this whenever someone wants to "showcase", "demo", "present", "screen-record", "make a video of" or "make a looping slideshow of" something using Quarto/revealjs, asks about revealjs iframe backgrounds, transitions, auto-slide, auto-animate, or wants to turn a revealjs deck into a video or GIF-like loop.
---

# Quarto revealjs showcase decks

A revealjs deck is a good way to stage a showcase: each slide is a "scene" (a live page, a screenshot, an animated layout), Quarto handles the authoring, and the result can be presented live, left looping on a screen, or recorded to video. This skill is the workflow plus the hard-won gotchas. Recipes are in `references/deck-recipes.md`, failure modes in `references/gotchas.md`, and the video capture tool is `scripts/capture_loop.py`.

## Workflow

1. **Plan scenes, not slides.** One scene per thing worth seeing: the default state, then variations (options, themes, sizes, data subsets). Decide up front whether the deck is for live presenting, an unattended loop, or video, because that changes the chrome and timing choices below.
2. **Build the deck** (see `references/deck-recipes.md`).
   - Use `background-iframe` for live pages (add `background-interactive="true"` if people should be able to use them), or `background-image`/`background-video` for static media.
   - Put any explanation in a small caption overlay at the bottom so the content stays visible. Hide the slide's own `##` title text with CSS when the background is the content.
   - Turn off chrome you don't want: `menu: false`, `progress: false`, `slide-number: false`, and the auto-slide pause button (CSS, needs `!important`).
   - For a deck driven by URL parameters, one iframe per variation is cheap to author and each variation is just a different query string.
3. **Add motion.**
   - Auto-advance with `auto-slide: <ms>` and `loop: true`. Budget the transition inside the slide time (a `slow` transition is about 1.2 s of a 4 s slide).
   - Choose transitions per slide with `transition=` and `background-transition=` (set both so the caption moves with its background). Control speed with `transition-speed: fast | default | slow`.
   - Use `auto-animate=true` for slides where the same elements (matched by `data-id`) should morph between layouts.
   - Preload iframes (`preload-iframes: true` plus `view-distance` at least the slide count) so every scene is already loaded when it arrives.
4. **Verify.** Render and look at every slide at a realistic size, once per slide, at a stable moment (not mid-transition). Check caption legibility, contrast against the busiest backgrounds, and that every iframe actually loaded. See the verification notes in `references/gotchas.md`, including the case where the built-in browser pane blocks the iframe origin.
5. **Capture video if wanted.** Run `scripts/capture_loop.py` (below). Always inspect a contact sheet of frames from the result before reporting it done.
6. **Report honestly.** Say what was verified in a real render versus only inferred, and call out anything that depends on the network, on viewport size, or on a setting you did not watch play.

## Capturing a video

`scripts/capture_loop.py URL OUTPUT.mp4` drives headless Chromium, records Chrome screencast frames as high-quality JPEGs, resamples them to a constant 30 fps, and encodes with ffmpeg. In the default `loop` mode it discards the first pass (which pays the loading cost) and keeps the second pass, from one wrap to slide 1 to the next, so the clip is fully loaded and loops seamlessly.

```bash
python3 ~/.claude/skills/quarto-revealjs-showcase/scripts/capture_loop.py http://localhost:8000/index.html out.mp4
python3 .../capture_loop.py URL out.mp4 --mode seconds --seconds 20 --warmup 8   # fixed length, no loop needed
```

Needs python with `playwright` and a Chromium build, plus `ffmpeg`. If `import playwright` fails, `python3` is probably resolving to a Python without it (check `which -a python3`; a pyenv shim path often has it). Serve the rendered deck over HTTP (`quarto preview`, or `python3 -m http.server --directory <dir>`) rather than `file://`.

Do not use Playwright's `record_video`: it writes a low-bitrate VP8 stream that looks grainy and cannot be fixed by re-encoding. Do not assemble variable-rate screencast frames with ffmpeg's concat demuxer: it gives the last frame a bogus extra duration. The script avoids both.

## Things to decide with the user, not assume

- Where the finished files go (deck folder, video location).
- Whether it will be published or only recorded locally, since that decides whether network dependence (iframes pointing at a live site) and preload weight matter.
- Whether the deck is presenter-driven or unattended, which decides `auto-slide`, controls, and whether captions are needed at all.
