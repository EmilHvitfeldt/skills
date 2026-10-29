---
name: html-short-video
description: Build a short-form vertical (9:16) promo video from a script using plain HTML, CSS and JavaScript animations, then record it to MP4 with a headless browser. Covers storyboarding for human review, reusing existing brand assets (stickers, logos, photos), applying a brand guide, layout and legibility rules for phones, panning over a pre-rendered image instead of live canvas, and recording a video that loops exactly. Use this whenever someone wants a short social video, reel, short or looping clip made from a script or text with code instead of a video editor, especially when assets like logos, stickers or photos already exist, or when they say "storyboard", "vertical video", "record the animation to mp4" or "make it loop".
---

# HTML short video

Turn a script into a short vertical video made from one self-contained HTML file with timed scenes, then capture it to MP4. No animation library is needed: CSS transforms, transitions and the Web Animations API are enough.

## 1. Plan before building

Read the script and the asset folders first, then present a storyboard for human review before writing any animation code. Do not start building until the person has seen it.

The storyboard lists, per scene: time range, what is on screen, how it animates, and the on-screen text. Keep the total around 30 to 40 seconds.

Ask these up front, in one message, so the plan is right the first time:

- Is there a voiceover? If a human will read it, produce no audio and add a timing guide at the end. If audio is wanted, ask which service and what the budget is.
- Background style: plain CSS gradients (free, simple) or generated imagery.
- Output: format, resolution and aspect ratio. Default for short-form is 1080x1920, 30 fps.
- Would real people photos help? Say which scene would use them and what kind of photo, and let the person supply them. Do not generate or draw people.
- Time and cost limits, if any. Track them and report at the end.

Prefer assets that already exist (stickers, logos, photos, screenshots) over generating or drawing new ones.

## 2. Brand guidelines

If the person has a brand guide or brand skill, apply it from the first build, not as a later pass. Ask for it during planning.

- A packaged skill file (`.skill`) is usually a zip archive. If the brand skill is not installed, extract it into its own new directory and read the guide, fonts, colors and logos from there.
- Load fonts with `@font-face` from the extracted files and define colors as CSS variables.
- Follow the guide's rules on typography weight, casing, emoji, accent color usage and contrast. Check text contrast against the background (WCAG AA at least).
- Use the accent color sparingly, for emphasis only.

## 3. Build rules

Use one HTML file, a list of scenes with durations, and a single function that shows one scene at a time.

- **Verify every asset path exists** before referencing it. List the folder and match filenames exactly, including case and extension. A missing file otherwise fails silently as a blank spot.
- **Preserve aspect ratios.** Read the real pixel dimensions of image assets (for example with `identify -format "%wx%h"`) and size from those. Hexagon-style or irregular assets look wrong if squeezed into a square.
- **Design for phones.** Text that looks fine on a desktop preview is too small on a phone. As a starting point at 1080 wide: headlines 90 to 110 px, sub-headlines about 75 px, body about 48 px, smallest text about 38 px. Make the main assets large too.
- **Recompute layout when anything scales.** When you enlarge elements, re-derive the spacing (for example the radius of a circular arrangement) so they do not overlap. Scaling size without scaling spacing is the common cause of overlap.
- **Keep text and busy visuals apart.** If text sits over a dense grid of images, put the text in a band with a gradient scrim, and start the grid away from the text area.
- **Photos:** crop with `object-fit: cover` plus a tuned `object-position` so faces are never cut off. Look at every crop. Let the person decide the order, since they often reorder after seeing it.
- **Stagger entrances** (fade plus slide, small delays) and keep motion gentle. Small touches, such as items floating in before settling, are what people notice and ask to keep, so do not remove them when fixing something else.

### Do not render a big grid live in a canvas

A live canvas that draws many images and pans across them proved fragile: flicker, wrong proportions, and a blank render where only one image appeared. If a scene needs a large panning field (a wall of logos, an "ecosystem" view), render it once as a static image, ideally from an existing source such as a screenshot the person provides, and pan or zoom across that image with CSS. It is deterministic, looks better and records cleanly. Ask the person for the screenshot if there is an existing source.

## 4. Looping exactly

A loop is only seamless if the last frame matches the first frame and nothing visible happens at the seam.

- Never restart with a page reload. It flashes. Restart by calling a reset function that clears everything the animation created or toggled: injected elements, "show" classes, animation state, pan offsets, running timers and animation frames.
- Remove any extra delay before the restart, and make the loop period equal to the sum of scene durations.
- Design the end state so it fades or cuts naturally into the start state. If the first scene begins from an empty screen, the last scene should end on something that transitions cleanly to it.
- Timer-based sequencing drifts. For exact results, drive the animation from one clock (for example `performance.now()` or a single timeline) so a recording can start precisely at time zero.
- The first pass of the animation includes load time and initial delay that later passes do not. If recording in real time, let one full loop pass first and start recording exactly at the start of the next one, accounting for the initial delay. Verify the timing arithmetic, because being off by a fraction of a second drops the opening animation. If the person likes an opening animation, make sure the recording includes it.

## 5. Recording to MP4

A headless browser (Puppeteer) with a screen recorder package works. Set the viewport to the target resolution and device scale 1, wait for network idle and for fonts and images to load, then record for exactly one loop duration.

- Keep the recording script separate from the HTML, with the target file and loop duration as parameters, so re-recording after an edit is a single command.
- Run recordings in the background, since they take about as long as the video itself.
- Real-time recording can be uneven. If the output stutters, consider stepping the animation frame by frame and capturing screenshots to assemble with `ffmpeg`.
- **Always check the output**, not just that the file exists: duration, resolution and size with `ffprobe`, then extract the first and last frames with `ffmpeg` and look at both. They should match for a loop. Also look at a frame from each scene for overlap, cut-off faces and unreadable text. Preview the HTML in a browser before recording to catch problems cheaply.

## 6. Working with the person

- Make the changes asked for, then re-record only when asked, or offer to. Name the output file you changed.
- When the person reports "the hexes do not show up" or similar, check the console and asset paths first, and if the first fix does not work, propose the simpler approach rather than layering more debugging on the complex one.
- Report what you verified and what you did not. Do not claim a loop is seamless without comparing the first and last frames.

## 7. Deliverables

- The final MP4, named clearly, and the HTML source so it can be edited.
- The recording script.
- If a human will read the script aloud: a short timing guide listing each scene, its time range and the lines to read.
- A brief note listing time spent, cost, and any assets still wanted.
