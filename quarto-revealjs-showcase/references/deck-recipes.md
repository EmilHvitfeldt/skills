# Deck recipes

Copy-paste starting points. Everything here was exercised in a real Quarto 1.9 render unless marked otherwise.

## YAML for an unattended, looping showcase

```yaml
---
pagetitle: "My showcase"          # not `title`, which adds a title slide
format:
  revealjs:
    theme: [default, styles.scss]
    auto-slide: 4000              # ms per slide, including the transition
    loop: true
    transition: fade              # default; override per slide
    background-transition: fade
    transition-speed: slow        # fast | default | slow (~0.4 / 0.8 / 1.2 s)
    preload-iframes: true
    view-distance: 8              # at least the number of slides, or only nearby ones preload
    mobile-view-distance: 8
    menu: false
    progress: false
    slide-number: false
    controls: true                # false to hide the arrows too
    embed-resources: false
---
```

## Slides with live page backgrounds

```markdown
## Default {background-iframe="https://example.com/app/" background-interactive="true"}

::: {.overlay}
Caption text shown over the page.
:::

## Variation {transition="zoom" background-transition="zoom" background-iframe="https://example.com/app/?theme=dark"}
```

Other background types work the same way: `background-image="img.png"`, `background-video="clip.mp4"`, `background-color="#000"`.

## Caption overlay and chrome (styles.scss)

```scss
/*-- scss:rules --*/

// Black behind everything so gaps during transitions are not white.
// Do NOT include `.reveal .slides` here: it sits above the backgrounds and would cover iframes.
html, body, .reveal-viewport, .reveal, .reveal .backgrounds, .reveal .slide-background {
  background-color: #000;
}

// The background is the content, so hide the slide title text.
.reveal h2 { display: none; }

// Small caption pinned to the bottom.
.reveal .overlay {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  max-width: 80%;
  padding: 0.4em 0.9em;
  font-size: 1.125em;             // scales with the slide; check at the target resolution
  text-align: center;
  color: #fff;
  background: rgba(0, 0, 0, 0.85);
  border-radius: 8px;
  pointer-events: none;           // lets drag/scroll reach an interactive iframe
  code { color: #fff; background: transparent; font-size: 0.95em; }  // inline code defaults to dark indigo
  a { color: #9fc5e8; pointer-events: auto; }
}

// Hide the auto-slide pause button (needs !important to beat reveal's own CSS).
.reveal .playback { display: none !important; }
```

## Transitions

Built-in names: `none`, `fade`, `slide`, `convex`, `concave`, `zoom`. Set them per slide with both attributes so text and background move together:

```markdown
## Scene {transition="zoom" background-transition="zoom" transition-speed="fast"}
```

`transition-speed` also works per slide. For exact timing beyond the three presets, override `transition-duration` on `.reveal .slides > section` and `.reveal .slide-background` in SCSS (not exercised here).

Reveal also documents mixing in/out styles, for example `transition="convex-in fade-out"` (not tried here).

Shader-style transitions (the gl-transitions extension, GL Transitions) look great on text and images but **do not work with iframe backgrounds**; see `gotchas.md`. For iframe decks use the built-in set, or a CSS `clip-path` animation on the incoming background (masks the live iframe instead of photographing it).

## Auto-animate

Verified syntax: slides with `auto-animate=true` morph matching elements between consecutive slides. Match elements with `data-id`; Quarto adds a `data-id` to slide titles automatically.

```markdown
---
format:
  revealjs:
    auto-animate-duration: 1.5       # also -easing (ease-in-out etc.) and -unmatched (true|false)
---

## One {auto-animate=true}

::: {data-id="box" style="background:#447099; width:100px; height:100px;"}
:::

## Two {auto-animate=true}

::: {data-id="box" style="background:#447099; width:400px; height:300px; margin-left:300px;"}
:::
```

Rendered output was checked for the attributes and the `autoAnimateDuration/Easing/Unmatched` config; the motion itself was not watched. Per-slide overrides of duration, easing and unmatched are documented by Reveal as slide attributes (not tried here). The capture script runs in real time, so auto-animate motion is recorded as it plays.

## Serving and rendering

```bash
quarto preview index.qmd                      # watches the .qmd only; touch it after editing .scss
quarto render index.qmd                       # static output: index.html + index_files/
python3 -m http.server 8000 --directory .     # serve the static render for capture
```
