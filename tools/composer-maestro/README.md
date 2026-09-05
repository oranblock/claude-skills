# Composer Maestro

Dependency-stack architects for five platforms. Each script resolves **live** versions from that
platform's real registry, then emits a ready-to-use manifest — no hand-copied version numbers,
no stale blog-post stacks.

Every composer ships four app presets — `food`, `ecommerce`, `chat`, `standard` — so the stack
you get is shaped by what you are building, not by a generic starter template.

## The composers

| Script | Platform | Registry | Manifest outputs |
|---|---|---|---|
| `composer_ultimate_starting_mystro.py` | Android (Compose/MAD) | Google Maven + Maven Central | `--toml`, `--dsl`, `--scaffold` |
| `composer_kmp.py` | Compose Multiplatform | Google Maven + Maven Central | `--toml`, `--dsl` |
| `composer_ios.py` | SwiftUI / SPM | GitHub release tags | `--package`, `--xcode` |
| `composer_web.py` | Next.js / React | npm registry | `--pkg`, `--install` |
| `composer_flutter.py` | Flutter / Dart | pub.dev | `--pubspec`, `--add` |

`composer_core.py` is the shared engine: HTTP, threaded resolution, version ranking, the stack
view, and the common CLI. The Android script predates it and remains standalone.

## Usage

```bash
python3 composer_web.py --app food                    # view the resolved stack
python3 composer_web.py --app food --pkg              # emit package.json
python3 composer_flutter.py --app chat --pubspec      # emit pubspec.yaml
python3 composer_ios.py --app standard --package      # emit Package.swift
python3 composer_kmp.py --app ecommerce --dsl         # emit build.gradle.kts

python3 composer_kmp.py --app food --agent-manifest   # JSON context for an LLM
python3 composer_web.py --app food --pkg -o package.json
python3 composer_flutter.py --app food --offline      # curated versions, no network
```

Every composer takes `--app`, `--agent-manifest`, `--offline`, and `-o FILE`.

**Banners and progress go to stderr; generated output goes to stdout.** So the manifest pipes
cleanly without `-o`:

```bash
python3 composer_kmp.py --app food --agent-manifest | jq '.resolved_at_versions'
python3 composer_web.py --app food --pkg > package.json
```

Emoji in the preset names are written through a UTF-8 reconfigured stdout and a UTF-8 file
handle, so the tools work with `LANG` unset, `PYTHONIOENCODING=ascii`, or a legacy Windows
console.

## How resolution works

1. Ask the platform's registry for the newest version.
2. Rank candidates by **parsed integer components**, so `1.10.0` beats `1.9.0` — string sorting
   gets this backwards, which is how stacks quietly regress a minor version.
3. Skip prereleases (`alpha`/`beta`/`rc`/`dev`/`snapshot`) — matched only at a separator, so a
   version like `1.0.0-devon` is not mistaken for a dev build and silently dropped.
4. On failure, fall back to a curated `STABLE_DEFAULTS` pin — and **label it** in the output as
   `[Curated Stable]` with a count, rather than passing it off as resolved.

That last point is the design rule: the tool always produces a complete, usable manifest, and
never lies about where a number came from.

## Platform notes

- **iOS** resolves from GitHub, because that is where SPM reads versions from — not a package
  registry. It asks `/releases/latest` first and only falls back to scanning tags, since GitHub
  returns tags in git order rather than version order: on a heavily-tagged repo the newest
  release sits outside the first page and a tag scan reports a confidently wrong version. A
  fallback result is labelled `GitHub (tag scan)` so you can tell the two apart. Unauthenticated
  GitHub allows ~60 requests/hour; set `GITHUB_TOKEN` to raise it. SwiftLint is emitted as a
  build-tool plugin, not a linkable product.
- **KMP** places each dependency in an explicit source set — `ktor-client-okhttp` in
  `androidMain`, `ktor-client-darwin` in `iosMain`. A JVM-only artifact in `commonMain` fails to
  resolve for the iOS target with an error that does not tell you that is the cause. Plugin
  versions (`kotlin`, `agp`, `composeMultiplatform`) are pinned in `TOOLCHAIN`, since they are
  not library coordinates.
- **Web** splits `dependencies` from `devDependencies` via `DEV_PACKAGES`.
- **Flutter** splits `dependencies` from `dev_dependencies` via `DEV_PACKAGES`, and emits caret
  constraints.

## Extending

Add a package to the relevant `CATALOGS[preset]["modules"]` section, and add a matching
`STABLE_DEFAULTS` entry so the offline path stays complete. A new platform needs a `CATALOGS`,
a `STABLE_DEFAULTS`, and one resolver of the shape `fn(pkg) -> (version | None, label | None)`.

## Requirements

Python 3.9+, standard library only. No pip install.
