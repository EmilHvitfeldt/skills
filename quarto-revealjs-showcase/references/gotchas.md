# Gotchas

Each of these cost real time in practice. Check them before debugging anything else.

## Deck authoring

- **`quarto preview` does not watch `.scss`.** Edits to the theme file do nothing until the `.qmd` changes. `touch index.qmd` to force a re-render, then reload.
- **Do not background-color `.reveal .slides`.** It sits above the background layer, so a black `.slides` box blanks out iframe/image backgrounds, leaving them visible only at the edges. Color `html, body, .reveal-viewport, .reveal, .backgrounds, .slide-background` instead.
- **A YAML `title:` adds a blank title slide.** Use `pagetitle:` for the browser tab title only.
- **Inline `code` in captions inherits a dark indigo** that is unreadable on a dark caption box. Set `color: #fff` on `code` inside the overlay.
- **The auto-slide pause button appears bottom-left** once `auto-slide` is set. Hide `.reveal .playback` with `display: none !important`; without `!important` reveal's CSS wins.
- **`auto-slide` pauses on user input** (`autoSlideStoppable` defaults to true). Interacting inside an iframe does not trigger it, so slides can change mid-drag.
- **Caption size is relative to the slide, which scales to the viewport.** About 30 px at the 1050x700 design size is about 18 px in a 640 px wide window. Judge legibility at the real target resolution.
- **`transition-speed: slow` is about 1.2 s.** With `auto-slide: 3000` that is over a third of each slide in motion; budget accordingly.
- **Preloading is heavy.** `preload-iframes: true` only preloads slides within `view-distance` (default 3). Raising it to the slide count loads every iframe at once, which can saturate the network on a deck of heavy pages. Fine for local recording, worth trimming for publishing.

## Transitions

- **Shader/canvas transition extensions (gl-transitions, html2canvas based) fail on iframe backgrounds.** They snapshot slides to a canvas, and html2canvas cannot capture iframe content. Symptom: the transition plays between blank white frames with only the caption visible, and the real content pops in after. This is independent of which shader you pick. Measure it directly by running `html2canvas(document.querySelector('.reveal'))` and checking how much of the result is non-white. They are fine for text, images and solid backgrounds.
- **Built-in transitions and CSS masks work with iframes** because the live iframe is moved or masked, never photographed.

## Verifying in the built-in browser pane

- **The pane can block external origins by policy** ("blocked by your organization's policy"). It may render an iframe origin for a while and then stop. If iframes come up blank, check this before suspecting the deck.
- **Do not try to swap iframe `src` at runtime to a local copy.** Reveal restores the original `src` on slide changes, so only some swaps stick. Instead render a throwaway copy of the deck (in a scratch directory) with local URLs and with preloading off, serve it, and test that.
- **`Reveal.configure({...})` at runtime can reset iframe backgrounds** (white screens afterwards). Configure through YAML and reload instead. `Reveal.configure({autoSlide: 0})` to pause auto-advance was fine.
- **Screenshots under an emulated custom viewport were unreliable** (cropped, white). Reset to the native pane size for screenshots.
- **Sample frames at stable moments.** A frame taken mid-transition is misleading (partial grids, tilted 3D slides, double text). Sample around 2 to 3 s into each slide.

## Video capture

- **`record_video` in Playwright is grainy.** Low-bitrate VP8, cannot be recovered by re-encoding.
- **The screencast frame size is CSS pixels** regardless of `device_scale_factor`, so the result is a 1080p capture even at scale 2. Scale 2 still renders crisper text and canvas content before the downscale. True 4K needs a different capture method.
- **Screencast is variable frame rate.** It only emits frames when the screen changes, so a static slide yields few frames. Resample to a constant rate by picking the latest frame at or before each output tick.
- **ffmpeg's concat demuxer gives the final frame a wrong long duration** (it borrowed the previous 2.8 s hold, making a 32 s loop come out 36 s). Build a numbered symlink sequence at the target fps and encode that instead; check `ffprobe` duration against the expected loop length.
- **First pass is not representative.** iframes and images load during it, so grids can be blank or partial. That is why loop mode keeps the second pass.
- **Loop boundaries are slide-change events** logged from `Reveal.on('slidechanged')`, using wall-clock time matched to the screencast timestamps. The clip starts on the transition into slide 1 and ends on the transition back to it, so it loops cleanly.
- **`python3` may not be the Python that has playwright.** PATH order can change between shells. Use `python3 -c 'import playwright'` to test and fall back to an explicit interpreter path.
- **Always look at the output.** Make a contact sheet (`ffmpeg ... -vf "select='eq(n\,75)+eq(n\,195)+...',scale=640:-1,tile=4x2"`) and read it, plus one full-resolution crop to judge sharpness. A first recording of this kind came out with every slide hidden behind a black box and looked fine in metadata.
