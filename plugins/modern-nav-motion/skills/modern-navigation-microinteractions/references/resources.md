# Resource Index

Curated, categorized, with a note on what each is actually good for. Entries marked ★ are the
ones worth reaching for first.

**Before recommending any of these into a shipping app:** check the license and the dependency
weight. A registry component that drags in a large animation runtime is a bad trade for a sliding
pill. Also verify the link is live if the recommendation matters — link rot is real and this list
is a snapshot.

---

## 1. Web — component registries and kits

| Resource | URL | Good for |
|---|---|---|
| ★ shadcn/ui | https://ui.shadcn.com/ | Copy-paste primitives you own; the baseline most other registries build on |
| ★ Motion (ex-Framer Motion) | https://motion.dev/ | The animation library itself — docs, examples, `layoutId` reference |
| ★ React Bits | https://reactbits.dev/ | 100+ animated components, 4 variants each (JS/TS × CSS/Tailwind), MIT |
| Aceternity UI | https://ui.aceternity.com/ | Showy hero/nav effects; heavy on visual flourish |
| Magic UI | https://magicui.design/ | Motion-driven components, pairs with shadcn |
| 21st.dev | https://21st.dev/ | Community registry, `npx shadcn add` compatible |
| Origin UI | https://originui.com/ | Tailwind + Radix, strong on form and nav primitives |
| Radix Primitives | https://www.radix-ui.com/primitives | Unstyled, accessible behaviour (tabs, nav menu) — use under any of the above |
| Headless UI | https://headlessui.com/ | Same idea, Tailwind Labs' version |
| Vaul | https://vaul.emilkowal.ski/ | Drawer/sheet with real gesture physics |
| Sonner | https://sonner.emilkowal.ski/ | Toasts done right; a good study in stacking animation |
| uiverse.io | https://uiverse.io/ | Pure-CSS component snippets; quality varies, good for ideas |
| React Router | https://reactrouter.com/home | Routing docs — `NavLink`, `useLocation` |
| Tailwind CSS | https://tailwindcss.com/docs | Utilities, logical properties, `rtl:` variants |

## 2. Web — animation engines

| Resource | URL | Good for |
|---|---|---|
| ★ Motion | https://motion.dev/ | Default choice for React |
| GSAP | https://gsap.com/ | Timeline-heavy sequences, SVG morphing, non-React |
| anime.js | https://animejs.com/ | Lightweight, framework-agnostic |
| Lottie (web) | https://lottiefiles.com/ | Designer-authored JSON animation |
| Rive | https://rive.app/ | State-machine driven interactive animation; better than Lottie for anything that responds to input |

---

## 3. Icons

| Resource | URL | Notes |
|---|---|---|
| ★ Lucide | https://lucide.dev/ | Clean, consistent, `strokeWidth` animatable, ISC license |
| ★ pqoqubbw icons | https://icons.pqoqubbw.dev/ | Lucide icons pre-wired with Motion animations |
| @animateicons/react | https://www.npmjs.com/package/@animateicons/react | Animated icon components via npm |
| Tabler Icons | https://tabler.io/icons | 5000+, MIT, outline and filled pairs (useful for selection states) |
| Phosphor Icons | https://phosphoricons.com/ | Six weights per icon — weight change is a free micro-interaction |
| Heroicons | https://heroicons.com/ | Tailwind's set; outline/solid pairs |
| Iconoir | https://iconoir.com/ | MIT, large, no attribution required |
| SF Symbols | https://developer.apple.com/sf-symbols/ | iOS/macOS only, but has native animation effects |
| Material Symbols | https://fonts.google.com/icons | Variable font axes (fill, weight, grade) — animate the axis, not the glyph |
| LucasBassetti SVG Animated Icons | https://github.com/LucasBassetti/svg-animated-icons | SVG animation reference implementations |
| ConvenientSolutions Animated SVG Icons | https://github.com/ConvenientSolutions/animated-svg-icons | As above |
| SVGator | https://svgator.com/ | GUI for authoring animated SVG (freemium) |

---

## 4. Android — Jetpack Compose

| Resource | URL | Good for |
|---|---|---|
| ★ Compose Animation docs | https://developer.android.com/develop/ui/compose/animation/introduction | The API decision tree — start here |
| ★ Navigation Compose | https://developer.android.com/develop/ui/compose/navigation | Type-safe routes, back stack, nested graphs |
| ★ Now in Android | https://github.com/android/nowinandroid | Production-grade reference app; read its nav module |
| Compose Samples | https://github.com/android/compose-samples | Jetsnack in particular has a good custom bottom bar |
| Android Platform Samples | https://github.com/android/platform-samples | Platform API demos incl. insets and predictive back |
| ★ Haze | https://github.com/chrisbanes/haze · https://chrisbanes.github.io/haze | Real backdrop blur for Compose (Android/iOS/Desktop/Web) |
| Exyte Animated Navigation Bar | https://github.com/exyte/animated-navigation-bar | Compose animated bar, good source to read even if not depended on |
| graphics-shapes | https://developer.android.com/develop/ui/compose/graphics/draw/shapes | `RoundedPolygon` + `Morph` for shape morphing without hand beziers |
| Lottie for Android | https://github.com/airbnb/lottie-android · https://airbnb.io/lottie/ | Designer-authored icon animation |
| Material 3 Motion | https://m3.material.io/styles/motion/overview | Google's easing/duration system; useful as a baseline to deviate from deliberately |
| Compose performance | https://developer.android.com/develop/ui/compose/performance | Recomposition, deferred reads, baseline profiles |
| Skydoves libraries | https://github.com/skydoves | Landscapist, Balloon, Orbital — well-built Compose UI libs |
| Vico | https://github.com/patrykandpatrick/vico | Charts, if the nav shell also needs data viz |
| Konfetti | https://github.com/DanielMartinus/Konfetti | Celebration particles; use once per app, at most |
| AndroidX source search | https://cs.android.com/androidx | When docs are ambiguous, read the actual implementation |

---

## 5. iOS — SwiftUI

| Resource | URL | Good for |
|---|---|---|
| ★ Human Interface Guidelines | https://developer.apple.com/design/human-interface-guidelines/ | What Apple expects a tab bar to do |
| ★ SwiftUI docs | https://developer.apple.com/documentation/swiftui/ | `matchedGeometryEffect`, `symbolEffect`, materials |
| SF Symbols | https://developer.apple.com/sf-symbols/ | The app + the animation effects catalogue |
| Hacking with Swift | https://www.hackingwithswift.com/quick-start/swiftui | Fast, reliable how-tos |
| The SwiftUI Lab | https://swiftui-lab.com/ | Deep dives on layout and animation internals |
| Exyte AnimatedTabBar | https://github.com/exyte/AnimatedTabBar | SwiftUI animated tab bar with several indicator styles |
| Lottie for iOS | https://github.com/airbnb/lottie-ios | Designer-authored animation |
| SwiftUI example projects | https://github.com/topics/swiftui-example | Grab-bag of community samples |

---

## 6. Cross-platform

| Resource | URL | Good for |
|---|---|---|
| Compose Multiplatform | https://www.jetbrains.com/compose-multiplatform/ | One Compose UI across Android/iOS/Desktop/Web |
| Rive | https://rive.app/ | One animation state machine, runtimes for all three platforms |
| Lottie | https://airbnb.io/lottie/ | Same JSON, all platforms; no interactivity |

---

## 7. Motion theory and tuning

| Resource | URL |
|---|---|
| Easing function reference | https://easings.net/ |
| Cubic bezier editor | https://cubic-bezier.com/ |
| Spring physics, friendly intro (Josh Comeau) | https://www.joshwcomeau.com/animation/a-friendly-introduction-to-spring-physics/ |
| Material 3 motion system | https://m3.material.io/styles/motion/overview |
| Apple HIG — Motion | https://developer.apple.com/design/human-interface-guidelines/motion |

---

## 8. Accessibility

| Resource | URL |
|---|---|
| ★ WAI-ARIA Authoring Practices (tabs, menus, disclosure) | https://www.w3.org/WAI/ARIA/apg/ |
| WCAG quick reference | https://www.w3.org/WAI/WCAG22/quickref/ |
| Android accessibility | https://developer.android.com/guide/topics/ui/accessibility |
| Apple accessibility | https://developer.apple.com/accessibility/ |
| Nielsen Norman Group | https://www.nngroup.com/ |

---

## 9. Color, type, and surface

| Resource | URL | Notes |
|---|---|---|
| OKLCH color picker | https://oklch.com/ | Perceptually uniform color — matters for animated tints |
| Coolors | https://coolors.co/ | Fast palette generation |
| Realtime Colors | https://realtimecolors.com/ | Preview a palette on a real UI before committing |
| Google Fonts | https://fonts.google.com/ | Includes strong Arabic families (Cairo, Tajawal, IBM Plex Sans Arabic) |
| Fontshare | https://www.fontshare.com/ | Free quality display faces |
| Haikei | https://haikei.app/ | Generated SVG backgrounds/blobs |

---

## 10. Inspiration

| Resource | URL | Notes |
|---|---|---|
| Dribbble | https://dribbble.com/ | Concept shots — most are not implementable as shown; treat as mood, not spec |
| Awwwards | https://www.awwwards.com/ | Web, heavy on motion |
| Mobbin | https://mobbin.com/ | Real shipped app screens; largely paywalled now |
| Godly | https://godly.website/ | Curated web design |
| Figma Community | https://www.figma.com/community | Editable files, incl. nav bar kits |

---

## 11. RTL / Arabic-specific

| Resource | URL | Notes |
|---|---|---|
| Material Design bidirectionality | https://m2.material.io/design/usability/bidirectionality.html | Which icons mirror and which don't — the definitive list |
| Android RTL support | https://developer.android.com/training/basics/supporting-devices/languages | Locale testing, `start`/`end` |
| MDN logical properties | https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_logical_properties_and_values | `inset-inline-start` etc. |
| Google Fonts Arabic | https://fonts.google.com/?subset=arabic | Cairo, Tajawal, Almarai, IBM Plex Sans Arabic |

---

## 12. Original source list (as supplied)

Preserved for provenance. All are folded into the categories above.

- React Router — https://reactrouter.com/home
- @animateicons/react — https://www.npmjs.com/package/@animateicons/react
- SwiftUI examples topic — https://github.com/topics/swiftui-example
- Android Platform Samples — https://github.com/android/platform-samples
- LucasBassetti SVG Animated Icons — https://github.com/LucasBassetti/svg-animated-icons
- ConvenientSolutions Animated SVG Icons — https://github.com/ConvenientSolutions/animated-svg-icons
- Aceternity UI — https://ui.aceternity.com/
- 21st.dev — https://21st.dev/
- Magic UI — https://magicui.design/
- Origin UI — https://originui.com/
- pqoqubbw icons — https://icons.pqoqubbw.dev/
- Exyte Animated Navigation Bar (Compose) — https://github.com/exyte/animated-navigation-bar
- Exyte AnimatedTabBar (SwiftUI) — https://github.com/exyte/AnimatedTabBar
