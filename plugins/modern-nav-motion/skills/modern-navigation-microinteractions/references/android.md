# Android — Jetpack Compose

Contents:
1. Stack and versions
2. Deriving selection from the back stack (type-safe nav)
3. Pattern A — floating pill dock
4. Pattern B — liquid cutout bar
5. Icon micro-animations
6. Blur / glassmorphism
7. Haptics
8. Insets, edge-to-edge, predictive back
9. RTL
10. Performance notes
11. Game overlays and non-standard shells

---

## 1. Stack and versions

100% Kotlin, Jetpack Compose, Navigation Compose, Material 3. Assume:

```kotlin
// libs.versions.toml — floors, not pins
compose-bom = "2024.09.00"        // or newer
navigation-compose = "2.8.0"      // 2.8.0+ required for type-safe routes
material3 = "1.3.0"
graphics-shapes = "1.0.0"         // androidx.graphics:graphics-shapes, for morphing shapes
```

API notes that bite:
- `Path.quadraticBezierTo` was renamed `Path.quadraticTo` in Compose 1.7. Use `quadraticTo`; if
  the project is older, swap the name back.
- `animateFloatAsState` requires a `label` for tooling since 1.5.
- `RenderEffect` blur (`Modifier.blur`) is API 31+. Below that it is a no-op — plan a fallback.
- `mutableIntStateOf` over `mutableStateOf(0)` for Int state; avoids autoboxing on a hot path.

---

## 2. Deriving selection from the back stack

Type-safe routes (Navigation 2.8+). Routes are `@Serializable` objects, not strings — the
compiler catches a renamed destination instead of a runtime crash on a typo.

```kotlin
import kotlinx.serialization.Serializable

@Serializable object Home
@Serializable object Units
@Serializable object Battles
@Serializable object Settings

data class NavItem(
    val route: Any,
    val icon: ImageVector,
    val label: String,
)

@Composable
fun rememberSelectedIndex(navController: NavController, items: List<NavItem>): Int {
    val backStackEntry by navController.currentBackStackEntryAsState()
    val destination = backStackEntry?.destination
    return remember(destination) {
        items.indexOfFirst { item ->
            destination?.hierarchy?.any { it.hasRoute(item.route::class) } == true
        }.coerceAtLeast(0)
    }
}
```

`hierarchy` matters: a nested graph's child destination should still light up its parent tab.
Checking `destination.route == item.route` directly fails the moment you nest anything.

Navigating from a tab — the four-line incantation that makes tabs behave like tabs:

```kotlin
fun NavController.navigateTab(route: Any) {
    navigate(route) {
        popUpTo(graph.findStartDestination().id) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}
```

Without `saveState`/`restoreState` the user loses scroll position on every tab switch, which
reads as a bug even though nothing crashed.

---

## 3. Pattern A — floating pill dock

Sliding pill indicator, spring-driven, position derived from measured item bounds so it survives
RTL and variable item counts.

```kotlin
@Composable
fun FloatingPillDock(
    items: List<NavItem>,
    selectedIndex: Int,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
    containerColor: Color = MaterialTheme.colorScheme.surfaceContainerHigh,
    indicatorColor: Color = MaterialTheme.colorScheme.primaryContainer,
) {
    var itemBounds by remember { mutableStateOf(mapOf<Int, Pair<Float, Float>>()) } // index -> (x, width)

    val target = itemBounds[selectedIndex]
    val indicatorX by animateFloatAsState(
        targetValue = target?.first ?: 0f,
        animationSpec = spring(dampingRatio = 0.8f, stiffness = Spring.StiffnessMediumLow),
        label = "indicatorX",
    )
    val indicatorW by animateFloatAsState(
        targetValue = target?.second ?: 0f,
        animationSpec = spring(dampingRatio = 0.9f, stiffness = Spring.StiffnessMediumLow),
        label = "indicatorW",
    )

    Box(
        modifier
            .padding(horizontal = 16.dp)
            .navigationBarsPadding()
            .padding(bottom = 12.dp)
            .shadow(20.dp, CircleShape, clip = false, ambientColor = Color.Black.copy(alpha = .25f))
            .clip(CircleShape)
            .background(containerColor)
            .height(64.dp)
            .fillMaxWidth(),
    ) {
        // Indicator drawn behind items, positioned via graphicsLayer (no relayout per frame)
        if (target != null) {
            Box(
                Modifier
                    .graphicsLayer { translationX = indicatorX }
                    .width(with(LocalDensity.current) { indicatorW.toDp() })
                    .fillMaxHeight()
                    .padding(vertical = 8.dp)
                    .clip(CircleShape)
                    .background(indicatorColor),
            )
        }

        Row(Modifier.fillMaxSize(), verticalAlignment = Alignment.CenterVertically) {
            items.forEachIndexed { index, item ->
                DockItem(
                    item = item,
                    selected = index == selectedIndex,
                    onClick = { onSelect(index) },
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .onGloballyPositioned { coords ->
                            val x = coords.positionInParent().x
                            val w = coords.size.width.toFloat()
                            if (itemBounds[index] != x to w) {
                                itemBounds = itemBounds + (index to (x to w))
                            }
                        },
                )
            }
        }
    }
}
```

`onGloballyPositioned` + `positionInParent()` is what makes this RTL-correct: the layout system
already mirrored the row, so the measured x is already right. Computing `index * itemWidth`
instead produces an indicator that slides the wrong way in Arabic.

---

## 4. Pattern B — liquid cutout bar

The bar's outline dips to cradle a raised active icon. The character of the curve is entirely in
the shoulder control points — `shoulder` below is the knob to tune first.

```kotlin
/**
 * @param cx        centre of the cutout, px, in bar-local coordinates
 * @param radius    half-width of the cradle, px
 * @param depth     how far the dip descends, px (negative = upward bulge)
 * @param shoulder  0.4f = tight notch, 1.0f = soft liquid meniscus
 */
private fun buildCutoutPath(
    size: Size,
    cx: Float,
    radius: Float,
    depth: Float,
    corner: Float,
    shoulder: Float = 0.85f,
): Path = Path().apply {
    val left = cx - radius * 1.7f
    val right = cx + radius * 1.7f
    val s = radius * shoulder

    moveTo(corner, 0f)
    lineTo(left, 0f)
    // descend into the cradle
    cubicTo(left + s, 0f, cx - radius, depth, cx, depth)
    // climb back out, mirrored
    cubicTo(cx + radius, depth, right - s, 0f, right, 0f)
    lineTo(size.width - corner, 0f)
    quadraticTo(size.width, 0f, size.width, corner)
    lineTo(size.width, size.height - corner)
    quadraticTo(size.width, size.height, size.width - corner, size.height)
    lineTo(corner, size.height)
    quadraticTo(0f, size.height, 0f, size.height - corner)
    lineTo(0f, corner)
    quadraticTo(0f, 0f, corner, 0f)
    close()
}

@Composable
fun LiquidCutoutBar(
    items: List<NavItem>,
    selectedIndex: Int,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
    barColor: Color = MaterialTheme.colorScheme.surfaceContainerHigh,
) {
    require(items.size in 2..5) { "Cutout bars degrade past 5 items — use a pill dock instead." }

    val density = LocalDensity.current
    var barSize by remember { mutableStateOf(Size.Zero) }
    val itemWidth = if (items.isEmpty()) 0f else barSize.width / items.size

    // Cutout centre follows selection with a slightly under-damped spring: the overshoot is what
    // makes it read as liquid rather than as a sliding cut-out rectangle.
    val cx by animateFloatAsState(
        targetValue = itemWidth * selectedIndex + itemWidth / 2f,
        animationSpec = spring(dampingRatio = 0.62f, stiffness = Spring.StiffnessMediumLow),
        label = "cutoutX",
    )

    Box(modifier.navigationBarsPadding()) {
        Canvas(
            Modifier
                .fillMaxWidth()
                .height(64.dp)
                .align(Alignment.BottomCenter)
                .onGloballyPositioned { barSize = it.size.toSize() },
        ) {
            val path = buildCutoutPath(
                size = size,
                cx = cx,
                radius = 34.dp.toPx(),
                depth = 26.dp.toPx(),
                corner = 28.dp.toPx(),
            )
            drawPath(path, barColor)
        }

        // Raised active icon, riding the cutout
        Box(
            Modifier
                .graphicsLayer {
                    translationX = cx - 28.dp.toPx()
                    translationY = -18.dp.toPx()
                }
                .size(56.dp)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.primary),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                items[selectedIndex].icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onPrimary,
            )
        }

        Row(
            Modifier.fillMaxWidth().height(64.dp).align(Alignment.BottomCenter),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            items.forEachIndexed { index, item ->
                val visible = index != selectedIndex
                val alpha by animateFloatAsState(if (visible) 1f else 0f, label = "itemAlpha")
                Box(
                    Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .graphicsLayer { this.alpha = alpha }
                        .clickable(
                            interactionSource = remember { MutableInteractionSource() },
                            indication = null,
                            enabled = visible,
                            onClick = { onSelect(index) },
                        )
                        .semantics {
                            role = Role.Tab
                            selected = !visible
                            contentDescription = item.label
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(item.icon, contentDescription = null)
                }
            }
        }
    }
}
```

Tuning order, in this priority: `dampingRatio` (0.55–0.70 for liquid) → `shoulder` → `depth` →
`radius`. Changing radius first sends people in circles because it changes the perceived depth.

Alternative worth knowing: `androidx.graphics.shapes` (`RoundedPolygon` + `Morph`) does
shape-to-shape morphing without hand-written beziers. Better for icon-shaped blobs; worse for a
cutout that must merge seamlessly with a straight bar edge.

---

## 5. Icon micro-animations

Three tiers, in ascending cost:

**Tier 1 — spring scale + tint.** Covers 80% of cases, zero assets.

```kotlin
val scale by animateFloatAsState(
    targetValue = if (selected) 1.18f else 1f,
    animationSpec = spring(dampingRatio = 0.42f, stiffness = Spring.StiffnessMedium),
    label = "iconScale",
)
Icon(
    item.icon,
    contentDescription = null,
    modifier = Modifier.graphicsLayer { scaleX = scale; scaleY = scale },
    tint = animateColorAsState(
        if (selected) MaterialTheme.colorScheme.onPrimaryContainer
        else MaterialTheme.colorScheme.onSurfaceVariant,
        label = "iconTint",
    ).value,
)
```

**Tier 2 — AnimatedVectorDrawable.** Real path morphing (outline → filled, hamburger → X).
Author the AVD in `res/drawable`, then:

```kotlin
val image = AnimatedImageVector.animatedVectorResource(R.drawable.avd_home)
Icon(
    painter = rememberAnimatedVectorPainter(image, atEnd = selected),
    contentDescription = null,
)
```

Requires `androidx.compose.animation:animation-graphics`. `atEnd` flips and the drawable plays;
it does not accept a progress value, so it cannot be scrubbed by a gesture.

**Tier 3 — Lottie.** For designer-authored motion you would never hand-code.

```kotlin
val composition by rememberLottieComposition(LottieCompositionSpec.RawRes(R.raw.nav_home))
val progress by animateLottieCompositionAsState(composition, isPlaying = selected)
LottieAnimation(composition, { progress })
```

Cost: a runtime dependency plus JSON parsing. Do not use Lottie for a scale animation.

---

## 6. Blur / glassmorphism

Two options.

**Platform blur (API 31+)** — cheapest to adopt, no dependency:

```kotlin
val supportsBlur = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
Box(
    Modifier
        .clip(CircleShape)
        .then(if (supportsBlur) Modifier.blur(24.dp) else Modifier)
        .background(barColor.copy(alpha = if (supportsBlur) 0.55f else 0.92f)),
)
```

Note `Modifier.blur` blurs the composable's *own* content, not what is behind it. For true
backdrop blur you need the content behind rendered into the same layer — which is what Haze does.

**Haze** (`dev.chrisbanes.haze`) — real backdrop blur, Compose Multiplatform, actively
maintained. Mark the background with `hazeSource`, the bar with `hazeEffect`. API surface has
changed across versions (`hazeChild` → `hazeEffect`), so check the docs at
https://chrisbanes.github.io/haze for the version you pull.

Always ship a non-blur fallback path and gate it on device tier if targeting budget Android.
A 24dp backdrop blur under a scrolling list is a measurable frame-time cost, not a free effect.

---

## 7. Haptics

Fire on *selection change*, never inside a composable body — that means every recomposition.

```kotlin
val haptics = LocalHapticFeedback.current
LaunchedEffect(selectedIndex) {
    haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
}
```

`TextHandleMove` is the light tick; `LongPress` is heavier. For finer control drop to the View
layer: `view.performHapticFeedback(HapticFeedbackConstants.CONTEXT_CLICK)`. Skip the first
emission if you don't want a buzz on screen entry — guard with a `remember { false }` flag.

---

## 8. Insets, edge-to-edge, predictive back

- Call `enableEdgeToEdge()` in `onCreate`. It is required behaviour on Android 15+, not optional.
- A floating bar needs `Modifier.navigationBarsPadding()` (gesture nav pill) plus its own bottom
  margin. Without it the bar sits under the system pill on some devices and looks fine on yours.
- Content behind the bar needs bottom padding equal to bar height + margin, otherwise the last
  list item is permanently unreachable. Expose the bar height via a `CompositionLocal` or pass it
  down; hardcoding `80.dp` in two places guarantees drift.
- Predictive back (`android:enableOnBackInvokedCallback="true"`): if the bar animates on
  destination change, it must handle the *cancelled* back gesture too. Derived state handles this
  correctly for free; manually-driven state does not.
- IME: hide or translate the bar when the keyboard opens (`WindowInsets.ime`), or it floats
  absurdly above the keyboard.

---

## 9. RTL

```kotlin
val isRtl = LocalLayoutDirection.current == LayoutDirection.Rtl
```

- Prefer measured positions (`positionInParent()`) over computed indices — see §3.
- Mirror directional icons only: `Modifier.graphicsLayer { scaleX = if (isRtl) -1f else 1f }`
  applied to back/forward/send, never to home/search/settings.
- Use `start`/`end` padding, never `left`/`right`.
- Preview both directions:
  `@Preview(locale = "ar", showBackground = true)` alongside the default.

---

## 10. Performance notes

- Move the indicator with `Modifier.graphicsLayer { translationX = x }` where `x` is read inside
  the lambda — this defers the read to the draw phase and skips recomposition and relayout.
  `Modifier.offset { IntOffset(x.roundToInt(), 0) }` is the layout-phase equivalent and also fine;
  `Modifier.padding(start = x.dp)` is the wrong answer and will show up in a trace.
- Hoist `Path` objects with `remember` and mutate with `reset()` instead of allocating per frame.
- `derivedStateOf` for anything computed from scroll offset (e.g. hide-on-scroll bars), or the
  bar recomposes every scroll pixel.
- Enable a baseline profile for the nav module — first-launch jank on a nav bar is the first
  thing a user sees.
- Measure with Perfetto / Macrobenchmark `FrameTimingMetric`, not by watching it look smooth on
  a flagship.

---

## 11. Game overlays and non-standard shells

When Compose UI sits over a `SurfaceView`/`GLSurfaceView` game surface:

- Keep the Compose overlay in its own window layer and avoid recomposing it from the game loop.
  Push state across a `StateFlow` sampled at UI rate (e.g. `sample(100.milliseconds)`), not per
  frame — a 60Hz recomposition of a HUD will fight the renderer for the main thread.
- Prefer `Modifier.drawWithCache` / `Canvas` for HUD elements over deep composable trees; fewer
  nodes, fewer layout passes.
- Blur over a live game surface is expensive twice over; use a gradient scrim instead.
- Touch routing: mark non-interactive HUD areas so gestures fall through to the game surface
  rather than being eaten by an invisible full-screen Box.
- Test at the target frame budget with the game actually running. A nav overlay that costs 2ms is
  invisible in a menu and fatal in a 60fps battle scene.
