# iOS — SwiftUI

Contents:
1. Stack
2. Routing wiring
3. Pattern A — capsule tab bar (`matchedGeometryEffect`)
4. Pattern B — liquid cutout via Shape
5. SF Symbols micro-animations
6. Materials and blur
7. Haptics
8. Safe areas
9. RTL and Dynamic Type
10. Performance notes

---

## 1. Stack

SwiftUI + SF Symbols. Custom bars replace `TabView`'s chrome but usually keep its behaviour.

Version gates worth knowing:
- `.symbolEffect(_:value:)` — iOS 17+
- `.sensoryFeedback(_:trigger:)` — iOS 17+
- `.symbolEffect(.wiggle)`, `.rotate`, variable-value symbols — iOS 18+
- `@Observable` macro — iOS 17+ (replaces `ObservableObject`/`@Published`)

Below iOS 17, fall back to `UIImpactFeedbackGenerator` and manual scale animations.

---

## 2. Routing wiring

Single source of truth, whether that's a `TabView` selection binding or a `NavigationStack` path:

```swift
enum Tab: Hashable, CaseIterable {
    case home, units, battles, settings

    var symbol: String {
        switch self {
        case .home: "house"
        case .units: "person.3"
        case .battles: "shield.lefthalf.filled"
        case .settings: "gearshape"
        }
    }

    var title: String {
        switch self {
        case .home: "Home"
        case .units: "Units"
        case .battles: "Battles"
        case .settings: "Settings"
        }
    }
}

@Observable
final class Router {
    var tab: Tab = .home
    var paths: [Tab: NavigationPath] = [:]
}
```

Keeping a `NavigationPath` per tab is what makes tab re-selection able to pop to root — the
behaviour users expect and the first thing they notice missing.

---

## 3. Pattern A — capsule tab bar

`matchedGeometryEffect` is the SwiftUI equivalent of Motion's `layoutId`: render the highlight
only under the selected item and it flies between positions.

```swift
struct FloatingTabBar: View {
    @Binding var selection: Tab
    @Namespace private var ns
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var animation: Animation {
        reduceMotion ? .linear(duration: 0)
                     : .spring(response: 0.35, dampingFraction: 0.78)
    }

    var body: some View {
        HStack(spacing: 4) {
            ForEach(Tab.allCases, id: \.self) { tab in
                let isSelected = tab == selection

                Button {
                    withAnimation(animation) { selection = tab }
                } label: {
                    Image(systemName: tab.symbol)
                        .font(.system(size: 18, weight: isSelected ? .semibold : .regular))
                        .symbolVariant(isSelected ? .fill : .none)
                        .symbolEffect(.bounce, value: isSelected)
                        .foregroundStyle(isSelected ? Color.primary : .secondary)
                        .frame(maxWidth: .infinity, minHeight: 44)
                        .contentShape(Rectangle())
                        .background {
                            if isSelected {
                                Capsule()
                                    .fill(.thinMaterial)
                                    .matchedGeometryEffect(id: "tabPill", in: ns)
                            }
                        }
                }
                .buttonStyle(.plain)
                .accessibilityLabel(tab.title)
                .accessibilityAddTraits(isSelected ? [.isSelected, .isButton] : .isButton)
            }
        }
        .padding(6)
        .background(.ultraThinMaterial, in: Capsule())
        .overlay(Capsule().strokeBorder(.white.opacity(0.12)))
        .shadow(color: .black.opacity(0.18), radius: 18, y: 8)
        .padding(.horizontal, 16)
        .sensoryFeedback(.selection, trigger: selection)
    }
}
```

Notes:
- `minHeight: 44` plus `.contentShape(Rectangle())` is what makes the whole cell tappable rather
  than just the glyph.
- `.buttonStyle(.plain)` prevents the default press-dim from fighting the custom animation.
- The `@Namespace` must live on a view that survives selection changes — put it on the bar, not
  on a child that gets rebuilt.

---

## 4. Pattern B — liquid cutout via Shape

```swift
struct CutoutBar: Shape {
    var cx: CGFloat            // cutout centre
    var radius: CGFloat = 34
    var depth: CGFloat = 26
    var corner: CGFloat = 28
    var shoulder: CGFloat = 0.85

    // Makes cx animatable
    var animatableData: CGFloat {
        get { cx }
        set { cx = newValue }
    }

    func path(in rect: CGRect) -> Path {
        var p = Path()
        let left = cx - radius * 1.7
        let right = cx + radius * 1.7
        let s = radius * shoulder

        p.move(to: CGPoint(x: corner, y: 0))
        p.addLine(to: CGPoint(x: left, y: 0))
        p.addCurve(to: CGPoint(x: cx, y: depth),
                   control1: CGPoint(x: left + s, y: 0),
                   control2: CGPoint(x: cx - radius, y: depth))
        p.addCurve(to: CGPoint(x: right, y: 0),
                   control1: CGPoint(x: cx + radius, y: depth),
                   control2: CGPoint(x: right - s, y: 0))
        p.addLine(to: CGPoint(x: rect.maxX - corner, y: 0))
        p.addQuadCurve(to: CGPoint(x: rect.maxX, y: corner),
                       control: CGPoint(x: rect.maxX, y: 0))
        p.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY - corner))
        p.addQuadCurve(to: CGPoint(x: rect.maxX - corner, y: rect.maxY),
                       control: CGPoint(x: rect.maxX, y: rect.maxY))
        p.addLine(to: CGPoint(x: corner, y: rect.maxY))
        p.addQuadCurve(to: CGPoint(x: 0, y: rect.maxY - corner),
                       control: CGPoint(x: 0, y: rect.maxY))
        p.addLine(to: CGPoint(x: 0, y: corner))
        p.addQuadCurve(to: CGPoint(x: corner, y: 0), control: .zero)
        p.closeSubpath()
        return p
    }
}
```

`animatableData` is the whole trick — without it SwiftUI snaps the shape instead of interpolating
it. Drive it with `withAnimation(.spring(response: 0.4, dampingFraction: 0.62))` for the
under-damped liquid feel.

---

## 5. SF Symbols micro-animations

Native, free, and better than anything hand-rolled for standard glyphs:

```swift
.symbolEffect(.bounce, value: isSelected)          // discrete pop
.symbolEffect(.pulse, options: .repeating)          // attention, use sparingly
.symbolEffect(.variableColor.iterative)             // loading / signal
.symbolEffect(.wiggle, value: errorCount)           // iOS 18+
.contentTransition(.symbolEffect(.replace))         // play ⇄ pause style swap
```

`.symbolVariant(.fill)` toggled by selection gives a weight change for free and pairs well with
`.bounce`. Custom SVG icons lose all of this — a real argument for staying on SF Symbols for
system-chrome-like bars.

---

## 6. Materials and blur

`.ultraThinMaterial` / `.thinMaterial` / `.regularMaterial` are the correct tool; they adapt to
light/dark and to the content behind automatically. Hand-rolled blur via `UIVisualEffectView` is
almost never worth it now.

```swift
.background(.ultraThinMaterial, in: Capsule())
```

Materials pick up vibrancy for foreground text automatically when you use
`.foregroundStyle(.secondary)` rather than a hardcoded gray.

---

## 7. Haptics

```swift
.sensoryFeedback(.selection, trigger: selection)         // iOS 17+
.sensoryFeedback(.impact(weight: .light), trigger: tapCount)
```

Pre-iOS 17: prepare a `UISelectionFeedbackGenerator` once and call `selectionChanged()`; creating
one per tap adds latency to the first fire.

---

## 8. Safe areas

```swift
ZStack(alignment: .bottom) {
    content
        .safeAreaInset(edge: .bottom) { Color.clear.frame(height: 76) }
    FloatingTabBar(selection: $router.tab)
}
```

`.safeAreaInset` is the correct way to reserve space — it teaches scroll views about the bar so
content and scroll indicators both stop above it. Manual bottom padding does not.

---

## 9. RTL and Dynamic Type

- SwiftUI stacks mirror automatically; `matchedGeometryEffect` follows real frames, so it works
  in RTL with no changes. Verify with `.environment(\.layoutDirection, .rightToLeft)` in a preview.
- Use `.leading`/`.trailing`, never `.left`/`.right`.
- Test at `.accessibilityExtraExtraExtraLarge`. Labels under icons will need to drop or truncate;
  decide which explicitly rather than letting them clip.
- SF Symbols mirror directional glyphs automatically in RTL locales — one more reason to prefer
  them over custom assets.

---

## 10. Performance notes

- Keep the bar out of the view identity of the content it overlays; a bar rebuilt on every content
  update will drop its animation mid-flight.
- `.drawingGroup()` can help a complex bar with many overlapping effects, but it flattens
  interactivity — apply it to the decorative layer only, never the buttons.
- Avoid `.shadow` on a large blurred container animating every frame; prefer a static shadow on a
  static container and animate the contents.
- Instruments → Animation Hitches template. Simulator frame timing is not evidence.
