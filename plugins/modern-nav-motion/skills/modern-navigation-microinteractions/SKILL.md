---
name: modern-navigation-microinteractions
description: Design and build floating navigation bars, pill/dock tab bars, liquid cutout indicators, morphing icons, and physics-driven micro-interactions across Jetpack Compose (Android), React/Tailwind/Motion (Web), SwiftUI (iOS), and Flutter. Use this skill whenever the user asks for a nav bar, tab bar, bottom bar, dock, sidebar, segmented control, animated icon, glassmorphism/blur UI, spring animation, page transition, or "make this UI feel more alive / less default" — even if they never say the words "navigation" or "micro-interaction". Also use it when reviewing existing nav/animation code for jank, accessibility, or RTL correctness, and when the user asks where to find good animated component libraries or icon sets.
---

# Modern Animated Navigation & Micro-Interactions

Elite cross-platform UI engineering for navigation shells and the small animations that make
them feel physical. Covers Compose, React, SwiftUI, and Flutter with the same underlying motion model,
so a design can be ported between platforms without re-deriving the physics.

## 1. Non-negotiables

**Routing state and presentation are separate layers.** The router owns "where am I"; the bar
owns "how does that look". Never store a `selectedIndex` that can drift from the back stack —
derive it. When a deep link, a system back gesture, or a programmatic `navigate()` changes the
destination, a derived bar updates for free and a duplicated one silently lies.

**Spring, not duration, is the default.** Interruptible spring animations survive a user who
taps three tabs in a row; a 300ms tween restarts and looks broken. Reach for a tween only for
non-interruptible, non-spatial properties (color, alpha, blur radius).

**One motion budget per interaction.** A tap can move the indicator, scale the icon, and fire a
haptic — that's three channels and it's the ceiling. Adding a color pulse and a label crossfade
on top reads as noise, not polish.

**Touch targets before beauty.** 48dp / 44pt minimum hit area regardless of how small the icon
renders. Shrink the visual, never the target.

**Respect reduced motion, everywhere.** Users who enable it get instant state changes or
cross-fades, not springs. This is one `if` per platform — see `references/motion-physics.md`.

## 2. Pick the reference file

Read the file for the platform in play — don't work from memory, the APIs move fast:

| Target | Read |
|---|---|
| Android / Jetpack Compose | `references/android.md` |
| Web / React + Tailwind + Motion | `references/web.md` |
| iOS / SwiftUI | `references/ios.md` |
| Flutter (Android + iOS) | `references/flutter.md` |
| Tuning feel, porting between platforms | `references/motion-physics.md` |
| Finding libraries, icon sets, inspiration | `references/resources.md` |

Building the same bar on two platforms? Read both platform files plus `motion-physics.md` and
match the damping ratio and travel distance, not the millisecond count.

## 3. Anatomy of a floating nav bar

Every implementation in this skill decomposes into the same six parts. Name them explicitly when
planning, and build them in this order — the indicator is where the perceived quality lives, so
it gets built and tuned before the decoration.

1. **Container** — floating surface, inset from screen edges, rounded to a capsule or large
   corner radius, elevated with a soft ambient shadow rather than a hard one.
2. **Surface treatment** — solid, translucent, or blurred. Blur costs real GPU time on mid-range
   Android; make it a flag you can turn off, not a hard dependency.
3. **Indicator** — the moving element: sliding pill, liquid cutout, morphing blob, or underline.
   Driven by the derived route state.
4. **Items** — icon + optional label, each an independent interaction target with its own press
   and selection state.
5. **Icon micro-animation** — scale, path morph, or symbol effect on selection change.
6. **Feedback** — haptic on selection change (not on every recomposition), optional sound off by
   default.

## 4. Indicator patterns

Choose deliberately; each has a different cost and a different failure mode.

**Sliding pill** — a rounded rect that translates behind the active item. Cheapest, most robust,
works with any item count, survives dynamic labels. Default choice.

**Liquid cutout / notch** — the bar's own outline dips to cradle a raised active icon. Highest
visual payoff, and the pattern most people mean by "liquid nav bar". Requires a custom `Path`
with bezier shoulders; the shoulder control points determine whether it reads as liquid or as a
notch cut with scissors. Breaks down past ~5 items and with variable-width labels.

**Morphing blob** — the indicator stretches toward the target before settling, like surface
tension. Implemented as a spring with low damping on the leading edge and higher damping on the
trailing edge, or as a width overshoot. Charming at 4 items, chaotic at 6.

**Expanding item** — the active item itself grows to a pill containing icon + label while
inactive items collapse to icon-only. Excellent for accessibility (the label is real text) and
for RTL, since layout does the work instead of manual coordinates.

Rule of thumb: if the item count is dynamic or user-configurable, use sliding pill or expanding
item. Cutouts assume a fixed, known layout.

## 5. Motion defaults

Starting values, not laws. Tune against a real device, not an emulator — spring perception is
frame-timing dependent.

| Feel | Damping ratio | Response | Where to use |
|---|---|---|---|
| Crisp, no overshoot | 1.0 | ~250ms | Sheets, anything under a finger |
| Default UI | 0.75–0.85 | ~350ms | Indicator travel, layout shifts |
| Playful | 0.5–0.65 | ~400ms | Icon pop, badge appearance |
| Bouncy / toy-like | 0.35–0.45 | ~500ms | Hero moments only, once per screen |

Cross-platform equivalents and the exact API calls are in `references/motion-physics.md`.

## 6. RTL and localization

Arabic, Hebrew, Farsi, and Urdu mirror the entire bar. This is the single most common bug in
copied nav-bar code, because indicator positions are usually computed in raw pixels from the
left edge.

- Compute indicator offsets from **layout coordinates**, never from `index * width` in a
  hardcoded LTR direction. In Compose read `LocalLayoutDirection`; on Web use logical properties
  (`inset-inline-start`, not `left`) and let Motion's `layoutId` handle it; in SwiftUI use
  `.environment(\.layoutDirection)` and native stacks.
- Directional icons (back, forward, send, next) must mirror; symmetric icons (home, settings,
  search) must not. Getting this backwards is worse than not mirroring at all.
- Test with the item labels in the longest supported language. German and Arabic both break
  layouts that were tuned on English.
- Arabic numerals in badges: decide once between Western (1,2,3) and Eastern Arabic (١,٢,٣) and
  apply consistently — mixing them inside one bar looks like a bug.

## 7. Performance guardrails

The bar renders on every frame of every screen. It's the last place to be careless.

- **Blur is not free.** On Android, `RenderEffect` blur is API 31+ and costs milliseconds per
  frame at large radii; provide a translucent-solid fallback and let the user's device tier pick.
  On Web, `backdrop-filter` over a scrolling list can force expensive repaints — test on a
  throttled CPU, not a desktop.
- **Never recompose the whole bar to move one indicator.** Drive position with a lambda-based
  modifier (`Modifier.graphicsLayer { translationX = x() }` in Compose) or a transform on the
  compositor thread (Web: `transform`, not `left`).
- **Shadows are expensive when animated.** Animate scale or elevation tint instead of
  re-rasterizing a large blur shadow every frame.
- **Icon animation should not allocate per frame.** Precompute paths, hoist `Path` objects,
  reuse `AnimatedVectorDrawable` painters.
- Profile before defending a choice: Android Studio's Layout Inspector + Perfetto, Chrome
  DevTools Performance panel, Instruments' Animation Hitches template.

## 8. Accessibility checklist

Run this before calling any nav bar done:

- Each item exposes a role (tab / button) and its selected state to the accessibility layer.
- Icon-only items have text labels for screen readers, not just tooltips.
- Contrast: the active indicator must not be the *only* signal of selection — pair it with icon
  weight, fill, or a label.
- Reduced-motion path tested with the OS setting actually enabled.
- Keyboard (Web, and Android with a physical keyboard): arrow keys move between tabs, Enter/Space
  activates, focus ring visible and not clipped by `overflow: hidden`.
- Dynamic type / font scale at 200% doesn't clip labels or collapse the bar.

## 9. Working method

1. Confirm the target platform(s), the item count, and whether the item set is fixed or dynamic.
2. Name the indicator pattern from §4 and say why, in one line.
3. Read the platform reference file, then write the component in one piece — routing wiring
   included, not left as `// TODO connect nav`.
4. State the tunable knobs explicitly at the end (damping, radius, cutout depth, blur toggle) so
   the user can adjust feel without re-reading the code.
5. Flag what will break: item-count limits, minimum API level, blur cost, RTL caveats.

Deliver complete, compiling code. Snippets with elided bodies are worse than useless for
animation work — the feel lives in exactly the parameters people tend to elide.

## 10. Source hygiene

`references/resources.md` indexes libraries, registries, and icon sets. Two rules when citing it:

- Link rot is real. If a recommendation matters to the user's decision, verify the URL is live
  before presenting it, and say so if a search wasn't possible.
- Copying a component from a registry means inheriting its license and its dependency tree.
  Check both before recommending it into a shipping app — a nav bar that drags in a 300KB
  animation runtime is a bad trade for a sliding pill.
