# Web — React + Tailwind + Motion

Contents:
1. Stack
2. Routing wiring
3. Pattern A — floating pill dock (`layoutId`)
4. Pattern B — liquid cutout via SVG
5. Icon micro-animations
6. Glassmorphism that doesn't tank scroll perf
7. Reduced motion
8. Accessibility (tabs pattern)
9. RTL
10. Performance notes

---

## 1. Stack

- **Motion** (`motion`, imported from `motion/react`) — the successor package to `framer-motion`.
  Older codebases import from `framer-motion`; the API for everything here is identical. Don't
  mix both packages in one app.
- **Tailwind** for layout and surface treatment.
- **React Router** (`react-router-dom`) or Next.js `<Link>` + `usePathname()`.

```bash
npm i motion react-router-dom
```

---

## 2. Routing wiring

Derive active state from the router, never from `useState`:

```jsx
// React Router
import { useLocation } from "react-router-dom";
const { pathname } = useLocation();
const activeIndex = items.findIndex((i) => pathname.startsWith(i.href));

// Next.js App Router
"use client";
import { usePathname } from "next/navigation";
const pathname = usePathname();
```

`startsWith` rather than `===` so nested routes (`/units/42`) keep the parent tab lit. Guard the
root: `/` matches everything with `startsWith`, so special-case it.

---

## 3. Pattern A — floating pill dock

`layoutId` does the heavy lifting: render the indicator only inside the active item and Motion
animates it between positions automatically, including on window resize and in RTL.

```jsx
import { motion, useReducedMotion } from "motion/react";
import { NavLink, useLocation } from "react-router-dom";
import { Home, Users, Swords, Settings } from "lucide-react";

const items = [
  { href: "/", label: "Home", Icon: Home },
  { href: "/units", label: "Units", Icon: Users },
  { href: "/battles", label: "Battles", Icon: Swords },
  { href: "/settings", label: "Settings", Icon: Settings },
];

const spring = { type: "spring", stiffness: 380, damping: 30, mass: 0.9 };

export function FloatingDock() {
  const { pathname } = useLocation();
  const reduce = useReducedMotion();

  const isActive = (href) => (href === "/" ? pathname === "/" : pathname.startsWith(href));

  return (
    <nav
      role="tablist"
      aria-label="Primary"
      className="fixed inset-x-4 bottom-[max(1rem,env(safe-area-inset-bottom))] z-50
                 mx-auto flex max-w-md items-center gap-1 rounded-full border
                 border-white/10 bg-white/70 p-1.5 shadow-lg shadow-black/10
                 backdrop-blur-md dark:bg-neutral-900/70"
    >
      {items.map(({ href, label, Icon }) => {
        const active = isActive(href);
        return (
          <NavLink
            key={href}
            to={href}
            role="tab"
            aria-selected={active}
            className="relative flex flex-1 items-center justify-center rounded-full
                       px-3 py-2.5 text-sm outline-none focus-visible:ring-2
                       focus-visible:ring-sky-500"
          >
            {active && (
              <motion.span
                layoutId="dock-pill"
                transition={reduce ? { duration: 0 } : spring}
                className="absolute inset-0 rounded-full bg-neutral-900/90 dark:bg-white/90"
                style={{ borderRadius: 9999 }}
              />
            )}
            <motion.span
              animate={reduce ? {} : { scale: active ? 1.12 : 1 }}
              transition={{ type: "spring", stiffness: 420, damping: 18 }}
              className="relative z-10 flex items-center gap-2"
            >
              <Icon
                className={`size-5 ${active ? "text-white dark:text-neutral-900" : "text-neutral-500"}`}
                strokeWidth={active ? 2.4 : 1.9}
                aria-hidden
              />
              <span className="sr-only">{label}</span>
            </motion.span>
          </NavLink>
        );
      })}
    </nav>
  );
}
```

Gotchas that cost people an hour each:

- **`borderRadius` must be in `style`, not only in a Tailwind class**, or Motion interpolates the
  layout box and the pill visibly squares off mid-flight.
- **`layoutId` must be unique per dock instance.** Two docks on one page with the same id will
  animate the pill between them across the screen.
- Wrap in `<LayoutGroup>` if the dock lives inside another layout-animating tree.
- `strokeWidth` is animatable on Lucide icons and is a cheaper "weight" signal than swapping to a
  filled variant.

---

## 4. Pattern B — liquid cutout via SVG

CSS can't cut a smooth notch out of a blurred surface. Draw the bar as an SVG path and animate
the path's `d` — Motion interpolates `d` when the point count matches.

```jsx
import { motion } from "motion/react";

const W = 400, H = 64, R = 28;

function cutoutPath(cx, radius = 34, depth = 26, shoulder = 0.85) {
  const left = cx - radius * 1.7;
  const right = cx + radius * 1.7;
  const s = radius * shoulder;
  return `
    M ${R} 0
    L ${left} 0
    C ${left + s} 0, ${cx - radius} ${depth}, ${cx} ${depth}
    C ${cx + radius} ${depth}, ${right - s} 0, ${right} 0
    L ${W - R} 0
    Q ${W} 0, ${W} ${R}
    L ${W} ${H - R}
    Q ${W} ${H}, ${W - R} ${H}
    L ${R} ${H}
    Q 0 ${H}, 0 ${H - R}
    L 0 ${R}
    Q 0 0, ${R} 0
    Z`;
}

export function LiquidBar({ activeIndex, count = 4 }) {
  const cx = (W / count) * activeIndex + W / count / 2;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full drop-shadow-lg" aria-hidden>
      <motion.path
        d={cutoutPath(cx)}
        animate={{ d: cutoutPath(cx) }}
        transition={{ type: "spring", stiffness: 300, damping: 22 }}
        className="fill-neutral-900"
      />
    </svg>
  );
}
```

Keep the command sequence identical between states — same number of `C`/`Q`/`L` commands, same
order — or interpolation falls back to a hard swap. If shapes must differ structurally, use
`flubber` to normalize them, or animate a single `cx` value through the path generator as above.

The raised icon sits in a separate absolutely-positioned element animated with `x`, not inside
the SVG, so it can carry real focus and click targets.

---

## 5. Icon micro-animations

- **Cheapest:** animate `strokeWidth`, `scale`, and `rotate` on a Lucide/Tabler icon. No new
  dependency, works with any icon set.
- **Path morphing:** an SVG icon with two path states plus `motion.path` and matching point
  counts. Same rule as §4.
- **Prebuilt sets:** `@animateicons/react` and `icons.pqoqubbw.dev` ship Lucide icons with
  hover/tap animations already wired. Copy the component rather than adding the dependency if you
  only need three icons.

Hover animations are pointer-only. Gate them so touch users don't get a stuck hover state:

```jsx
const canHover = window.matchMedia("(hover: hover)").matches;
```

---

## 6. Glassmorphism that doesn't tank scroll perf

`backdrop-blur` forces the browser to sample and blur everything behind the element on every
frame the backdrop changes — i.e. all the way through a scroll.

- Keep the blurred element small and `position: fixed`.
- Add `will-change: backdrop-filter` sparingly; it costs memory, so only on the one bar.
- Give the surface real opacity (`bg-white/70`) so the blur radius can stay low (`backdrop-blur-md`,
  not `-3xl`).
- Test on a throttled CPU in DevTools. A dock that's smooth on a desktop can be 20fps on a
  mid-range Android browser.
- Safari renders `backdrop-filter` differently and needs `-webkit-backdrop-filter`; Tailwind emits
  both, hand-written CSS often doesn't.

---

## 7. Reduced motion

```jsx
const reduce = useReducedMotion();
transition={reduce ? { duration: 0 } : spring}
```

Reduced motion means *no spatial travel*, not *no feedback*. Keep opacity and color transitions;
drop the sliding, the overshoot, and any parallax.

---

## 8. Accessibility (tabs pattern)

If the bar switches views in place it's a tablist; if it's site navigation it's a `<nav>` with
links and `aria-current="page"`. Pick one, don't mix the vocabularies.

For the tablist form:
- `role="tablist"` on the container, `role="tab"` + `aria-selected` on each item.
- Roving tabindex: only the active tab is `tabIndex={0}`, the rest `-1`; arrow keys move focus.
- `aria-controls` pointing at the panel, `role="tabpanel"` + `aria-labelledby` on it.
- Focus ring must be visible and not clipped — `overflow-hidden` on a rounded container will eat
  it. Use `focus-visible:ring-2` plus enough padding.

Reference the WAI-ARIA Authoring Practices tabs pattern rather than improvising.

---

## 9. RTL

- Set `dir="rtl"` on `<html>` and use logical Tailwind utilities: `ps-4`/`pe-4` over `pl-4`/`pr-4`,
  `start-0` over `left-0`.
- `layoutId` handles mirrored positions automatically because it reads real layout boxes — one
  more reason to prefer it over a manually animated `x` offset.
- Mirror directional icons with `rtl:-scale-x-100`; leave symmetric icons alone.

---

## 10. Performance notes

- Animate `transform` and `opacity` only. Animating `left`/`top`/`width` triggers layout on every
  frame.
- `layout` animations are relatively expensive — one `layoutId` per dock, not one per element.
- Memoize the items array outside the component or with `useMemo`; recreating it re-renders every
  `NavLink` on every route change.
- Lazy-load Lottie/Rive if used at all; they're heavy runtimes for what is usually a 12-line
  spring.
