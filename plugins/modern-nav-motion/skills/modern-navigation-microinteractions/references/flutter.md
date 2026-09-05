# Flutter — Animated Navigation & Micro-Interactions

Flutter's animation layer is imperative by default and declarative only if you build it that
way. The single biggest quality difference between a stock `BottomNavigationBar` and a nav bar
that feels designed is whether the indicator is driven by a physics simulation or by a
`Curves.easeInOut` tween that restarts on every tap.

---

## 1. Routing state is the source of truth

With `go_router`, derive the selected index from the current location — never store it:

```dart
int _indexFor(String location) {
  if (location.startsWith('/search')) return 1;
  if (location.startsWith('/library')) return 2;
  return 0;
}

// In build:
final index = _indexFor(GoRouterState.of(context).uri.path);
```

Use `StatefulShellRoute.indexedStack` when each tab needs its own preserved back stack. The
shell hands you `navigationShell.currentIndex` — that is the derived value; pass it to the bar
and call `navigationShell.goBranch(i)` on tap. A `setState(() => _selected = i)` next to a
router call is the duplicated-state bug from §1 of the parent skill.

---

## 2. Spring-driven indicator

`SpringSimulation` is the Flutter equivalent of Compose's `spring()`. Drive it through an
`AnimationController` with `animateWith`, so an in-flight animation is retargeted from its
current velocity instead of snapping:

```dart
class _IndicatorState extends State<Indicator> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController.unbounded(vsync: this);
  double _target = 0;

  static const _spring = SpringDescription(mass: 1, stiffness: 380, damping: 30); // ζ ≈ 0.77

  void _moveTo(double x) {
    _target = x;
    if (MediaQuery.disableAnimationsOf(context)) {
      _c.value = x;
      return;
    }
    _c.animateWith(SpringSimulation(_spring, _c.value, x, _c.velocity));
  }

  @override
  void dispose() { _c.dispose(); super.dispose(); }
}
```

`damping` here is absolute, exactly like Motion on the web, so the conversion table in
`motion-physics.md` transfers one-to-one: `ζ = damping / (2 * sqrt(stiffness * mass))`.

Render the moving pill with `AnimatedBuilder` wrapping *only* the indicator, and position it
with `Transform.translate` — not by rebuilding a `Row` with new `Padding`. Rebuilding the row
re-lays out every item each frame; the transform is paint-only.

---

## 3. Measuring item positions (RTL-safe)

Never compute `index * itemWidth`. Read real geometry so mirroring and variable label widths
work for free:

These keys must live on the `State`, not in `build`. A fresh `GlobalKey` every frame detaches
and re-attaches every item — losing their state and invalidating the measurement you just took.

```dart
// Field on the State object, not a local in build():
late final List<GlobalKey> _keys = List.generate(items.length, (_) => GlobalKey());

Rect _rectOf(GlobalKey key, RenderBox bar) {
  final box = key.currentContext!.findRenderObject() as RenderBox;
  final topLeft = box.localToGlobal(Offset.zero, ancestor: bar);
  return topLeft & box.size;
}
```

Schedule the first measurement in `WidgetsBinding.instance.addPostFrameCallback` and re-measure
on `LayoutBuilder` constraint changes and on locale change. If `items` can change length,
rebuild `_keys` in `didUpdateWidget` rather than making the list `late final`.

`Directionality.of(context)` tells you the direction; because these are laid-out coordinates,
you usually do not need to branch on it at all — which is the point.

For directional icons, mirror explicitly:

```dart
Transform.flip(flipX: Directionality.of(context) == TextDirection.rtl, child: icon)
```

---

## 4. Liquid cutout

The cutout is a `CustomClipper<Path>` (or `CustomPainter` if you want a stroked rim) whose notch
centre is the animated indicator position. Bezier shoulders decide whether it reads as liquid:

```dart
class NotchClipper extends CustomClipper<Path> {
  NotchClipper({required this.cx, required this.radius, required this.corner})
      : super(reclip: null);
  final double cx, radius, corner;

  @override
  Path getClip(Size size) {
    const shoulder = 1.6; // 1.4–1.8 reads liquid; 1.0 reads like scissors
    final w = radius * shoulder;
    return Path()
      ..moveTo(0, corner)
      ..quadraticBezierTo(0, 0, corner, 0)
      ..lineTo(cx - w, 0)
      ..cubicTo(cx - w * 0.5, 0, cx - radius, radius * 1.1, cx, radius * 1.1)
      ..cubicTo(cx + radius, radius * 1.1, cx + w * 0.5, 0, cx + w, 0)
      ..lineTo(size.width - corner, 0)
      ..quadraticBezierTo(size.width, 0, size.width, corner)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
  }

  @override
  bool shouldReclip(NotchClipper old) => old.cx != cx || old.radius != radius;
}
```

`shouldReclip` comparing fields is not optional — returning `true` unconditionally re-clips every
frame of every screen.

---

## 5. Blur and elevation

`BackdropFilter` is the most expensive widget most apps ship. Rules:

- Always wrap it in a `ClipRRect` — an unclipped backdrop filter samples the whole layer tree.
- Make the radius a parameter and expose an off switch; fall back to
  `Theme.of(context).colorScheme.surface.withValues(alpha: 0.92)` on low-tier devices.
  `withValues` needs Flutter 3.27+; below that use `.withOpacity(0.92)`.
- Prefer one blur for the whole bar over one per item.
- **Wrap the bar in a `RepaintBoundary`.** It paints above every screen, so without one, the
  scrolling content underneath repaints the bar on every frame and the bar's own indicator
  animation dirties the content layer. This is the cheapest win available here — one widget.
- Use `Material(elevation:)` or a single soft `BoxShadow`; animating `blurRadius` on a shadow
  re-rasterizes it every frame. Animate `scale` or the shadow's colour alpha instead.

Check the cost with `flutter run --profile` plus DevTools' Performance overlay, and enable
"Track widget rebuilds" to prove the bar is not rebuilding wholesale.

---

## 6. Haptics and feedback

```dart
if (newIndex != oldIndex) HapticFeedback.selectionClick();
```

Fire it in the tap handler, never in `build` — a rebuild is not a user action. On Android,
`HapticFeedback.selectionClick()` is a no-op on some devices; do not use it as the only
confirmation of a state change.

---

## 7. Accessibility

- Wrap each item in `Semantics(button: true, selected: i == index, label: item.label)`. The
  `selected` flag is what TalkBack and VoiceOver announce as "selected"; an animated pill is
  invisible to them.
- Icon-only items still need `label`. A `Tooltip` is not a substitute.
- Honour `MediaQuery.disableAnimationsOf(context)` (reduced motion) — set the controller value
  directly, as in §2.
- Test at `MediaQuery.textScalerOf(context)` = 2.0. If labels clip, collapse to icon-only above
  a threshold rather than letting text overflow.
- Minimum 48dp hit area: give each item an `InkWell` inside a `SizedBox(height: 48)` even when
  the icon renders at 24dp.

---

## 8. Icon micro-animation

- **Scale pop** — an `AnimationController` per item is wasteful; use one controller and an
  `Interval`-shifted `CurvedAnimation`, or drive scale from the shared indicator animation.
- **Path morph** — `AnimatedIcon` covers a fixed handful of pairs. For anything else use
  Lottie (`lottie` package) or Rive; Rive gives you state machines and is the better choice if
  the icon has more than two states.
- Hoist `Path` and `Paint` objects to fields on the painter — allocating them inside `paint()`
  runs at 60–120 Hz.

---

## 9. Pitfalls specific to Flutter

- `AnimationController` without `dispose()` leaks a ticker and eventually throws.
- `SingleTickerProviderStateMixin` with two controllers throws an assertion in debug
  (`_ticker == null`) — use `TickerProviderStateMixin` when you need more than one.
- `AnimatedContainer` restarts on interruption; it is a tween, not a spring. Fine for colour,
  wrong for the indicator.
- `IndexedStack` keeps every tab alive; that is usually what you want for state preservation but
  it means offscreen tabs still rebuild on inherited-widget changes. Use `TickerMode` to pause
  their animations.
- Hot reload does not reset controllers — a bar that "feels wrong" after a reload may be fine on
  a cold start. Verify before tuning.
