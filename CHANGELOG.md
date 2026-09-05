# Changelog

## 1.1.1
- `flutter.md`: `Colors.surface` → `Theme.of(context).colorScheme.surface`, with the
  `withValues` 3.27+ floor and the `withOpacity` fallback noted.
- `flutter.md`: `GlobalKey` list is now a `State` field, with the per-frame-key failure spelled
  out and `didUpdateWidget` covered for dynamic item counts.
- `flutter.md`: corrected the `SingleTickerProviderStateMixin` pitfall — it throws a debug
  assertion, it does not fail silently.
- `flutter.md`: added `RepaintBoundary` to the performance rules.
- Manifests: added `license`, `homepage`, `repository`, `$schema`; moved the marketplace
  description to the top level; removed the duplicate `version` from the marketplace entry.
- CI: runs `claude plugin validate .`, and fails a PR that changes plugin content without a
  version bump. Validator no longer KeyErrors on incomplete manifests.
- README: corrected the update story — pinned versions gate updates, so releases must bump.

## 1.1.0
- Added `references/flutter.md`: go_router-derived selection, `SpringSimulation`-driven
  indicators, RTL-safe geometry measurement, liquid cutout `CustomClipper`, `BackdropFilter`
  cost rules, semantics, and Flutter-specific pitfalls.
- Added a Flutter column to the cross-platform spring table in `references/motion-physics.md`,
  plus the damping-ratio conversion note.
- Skill description and platform table now list Flutter.
- Packaged as a Claude Code plugin inside a marketplace repo for one-command install and updates.

## 1.0.0
- Initial skill: Compose, React/Motion and SwiftUI navigation shells and micro-interactions.
