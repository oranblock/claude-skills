# Motion Physics — Tuning and Porting

Read this when a design must feel the same on two platforms, or when "it looks fine but feels
wrong" and nobody can say why.

---

## 1. The two-parameter model

Every spring in every framework here reduces to the same two perceptual dials:

**Damping ratio (ζ)** — how much it overshoots.
- `ζ = 1.0` — critically damped. Arrives fast, never overshoots. Feels precise, slightly cold.
- `ζ < 1.0` — under-damped. Overshoots and settles back. This is where "alive" lives.
- `ζ > 1.0` — over-damped. Sluggish. Almost never what you want in UI.

**Response / stiffness** — how long it takes.
- Response is duration-like (seconds to reach the target on a critically damped spring).
- Stiffness is the raw spring constant. Higher = faster.

Mass is a third dial, but changing it is almost always a mistake — it interacts with both others
and makes the result impossible to reason about. Leave it at 1 and tune the other two.

---

## 2. Cross-platform parameter table

Same perceptual feel, three APIs:

| Feel | Compose | Motion (Web) | SwiftUI | Flutter (`SpringDescription`) |
|---|---|---|---|---|
| Crisp, no overshoot | `spring(1f, Spring.StiffnessMedium)` | `{ stiffness: 500, damping: 45 }` | `.spring(response: 0.25, dampingFraction: 1.0)` | `stiffness: 500, damping: 45` |
| Default UI | `spring(0.8f, Spring.StiffnessMediumLow)` | `{ stiffness: 380, damping: 30 }` | `.spring(response: 0.35, dampingFraction: 0.8)` | `stiffness: 380, damping: 30` |
| Playful | `spring(0.55f, Spring.StiffnessMediumLow)` | `{ stiffness: 320, damping: 18 }` | `.spring(response: 0.4, dampingFraction: 0.55)` | `stiffness: 320, damping: 18` |
| Liquid / blobby | `spring(0.42f, Spring.StiffnessLow)` | `{ stiffness: 260, damping: 12 }` | `.spring(response: 0.5, dampingFraction: 0.42)` | `stiffness: 260, damping: 12` |

Conversions when you have one and need the other:
- Motion's `damping` is absolute, not a ratio: `ζ = damping / (2 * sqrt(stiffness * mass))`.
  So `{stiffness: 380, damping: 30, mass: 1}` → ζ ≈ 0.77.
- SwiftUI's `dampingFraction` *is* ζ directly.
- Flutter's `SpringDescription.damping` is absolute like Motion's, so the same formula applies
  (mass defaults to 1 in the table above).
- Compose's `dampingRatio` *is* ζ directly. Named constants:
  `DampingRatioNoBouncy` = 1.0, `DampingRatioLowBouncy` ≈ 0.75, `DampingRatioMediumBouncy` ≈ 0.5,
  `DampingRatioHighBouncy` ≈ 0.2.
- Compose stiffness constants: `StiffnessHigh` = 10000, `StiffnessMedium` = 1500,
  `StiffnessMediumLow` = 400, `StiffnessLow` = 200, `StiffnessVeryLow` = 50.

---

## 3. When *not* to spring

Springs are for spatial properties under direct or implied manipulation. Use a tween for:

- **Color and alpha** — a bouncing color reads as a flicker. `tween(200)` / `duration: 0.2`.
- **Blur radius** — overshoot means momentarily blurring past the target, which is visible and ugly.
- **Anything that must finish at an exact time** — a synced sequence, a video-locked transition.
- **Progress indicators** — bouncing progress implies data that went backwards.

---

## 4. Interruption behaviour

The real reason to prefer springs: a spring interrupted mid-flight carries its current velocity
into the new animation. A tween restarts from zero velocity, producing a visible stutter every
time a user taps two tabs quickly.

Test it deliberately: tap tab 1 → tab 4 → tab 2 within half a second. If the indicator visibly
stops and restarts, the animation is a tween or the state is being reset instead of retargeted.

Compose: `animateFloatAsState` retargets correctly by default. Manual `Animatable` needs
`animateTo` (which preserves velocity), not `snapTo` then `animateTo`.

Motion: retargeting is automatic with `animate`/`layoutId`. Killing and remounting the element
loses velocity.

SwiftUI: `withAnimation` on a changed value retargets. Toggling the view's identity does not.

---

## 5. Travel distance vs duration

Perceived speed is distance-dependent. A pill crossing 300px at the same spring as one crossing
60px will feel slow. Two fixes:

1. Keep the spring and accept it — correct for physical realism, and what most systems do.
2. Scale response with distance for long travel: `response = base * (1 + distance / screenWidth * 0.4)`.
   Use sparingly; it breaks the illusion that the indicator is a real object.

Never scale by item index — that produces different feel for the same physical distance depending
on where in the bar you tapped.

---

## 6. Stagger and sequencing

For groups (icons animating in, menu items appearing):
- 20–40ms per item. Below 20ms it reads as simultaneous; above 60ms the last item feels late.
- Cap the total stagger at ~200ms regardless of count. Eight items at 40ms is already 320ms of
  waiting for the last one.
- Stagger on entry only. Staggered *exit* makes dismissal feel slow, which is the one thing users
  never forgive.

---

## 7. Reduced motion, precisely

The setting means "no vestibular triggers": no large spatial travel, no parallax, no zoom, no
rotation. It does not mean "no feedback".

Correct reduced-motion substitution:

| Normal | Reduced |
|---|---|
| Pill slides across bar | Pill cross-fades in place |
| Icon springs to 1.18× | Icon changes weight/fill instantly |
| Screen slides in | Screen fades in (150ms) |
| Blob morphs | Instant shape swap |

API per platform:
- Compose: `LocalAccessibilityManager` / read the system setting via
  `Settings.Global.ANIMATOR_DURATION_SCALE == 0f`.
- Web: `useReducedMotion()` from Motion, or `matchMedia("(prefers-reduced-motion: reduce)")`.
- SwiftUI: `@Environment(\.accessibilityReduceMotion)`.

---

## 8. Haptics as a motion channel

Haptics carry the same information as an animation and are subject to the same budget.

- One haptic per discrete user-initiated state change. Not per frame, not per recomposition, not
  on programmatic navigation the user didn't trigger.
- Match weight to visual weight: a light tick for tab selection, a heavier impact for a
  destructive confirm.
- Always respect the system haptics setting; on Android it's per-device and honoured
  automatically by `performHapticFeedback`.
- Never fire haptics during scroll-driven animation — it turns into a buzz.

---

## 9. Debugging "it feels wrong"

Work down this list in order:

1. **Is it a tween pretending to be a spring?** Check interruption behaviour (§4).
2. **Is the state derived or duplicated?** A bar that occasionally animates from the wrong
   position has duplicated state that drifted.
3. **Is it dropping frames?** Feel and performance are indistinguishable to users. Profile before
   retuning parameters.
4. **Too many channels?** Count what moves on one tap. Over three, cut one.
5. **Is the overshoot fighting the shape?** Under-damped motion on a large, heavy-looking element
   reads as broken rather than playful. Bouncier for small elements, tighter for large ones.
6. **Only now**, adjust ζ — in 0.05 steps, not 0.3 jumps.
