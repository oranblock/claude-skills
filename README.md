# oranblock-skills — a Claude Code plugin marketplace

Install skills the same way you install anything else in Claude Code: add the marketplace once,
install the plugin, and Claude Code keeps it up to date from this repo.

## Install

```
/plugin marketplace add oranblock/claude-skills
/plugin install modern-nav-motion@oranblock-skills
```

The skill is then live in every project. If the install summary asks you to reload, run
`/reload-plugins`.

## Staying on the latest version

`plugins/modern-nav-motion/.claude-plugin/plugin.json` pins a `version`, and **Claude Code gates
updates on that field** — a push whose version is unchanged never reaches anyone who already
installed. So every release bumps it, and CI fails a PR that edits plugin content without a bump
(`.github/version-bumped.py`).

To pull the newest version:

```
/plugin marketplace update oranblock-skills
```

`/plugin` → *Manage marketplaces* shows your installed version against this repo's.

Versions are declared in `plugin.json` only. The marketplace entry deliberately has no
`version`: Claude Code always reads `plugin.json`'s value, so a second copy here could only
drift — the validator rejects one if it reappears.

## Plugins

### `modern-nav-motion` (v1.1.1)

Elite cross-platform navigation shells and micro-interactions — floating bars, pill/dock tab
bars, liquid cutout indicators, morphing icons, spring physics — with one shared motion model so
a design ports between platforms without re-deriving the feel.

Reference files, loaded on demand:

| Target | File |
|---|---|
| Android / Jetpack Compose | `references/android.md` |
| Web / React + Tailwind + Motion | `references/web.md` |
| iOS / SwiftUI | `references/ios.md` |
| Flutter (Android + iOS) | `references/flutter.md` |
| Tuning feel, porting between platforms | `references/motion-physics.md` |
| Libraries, icon sets, inspiration | `references/resources.md` |

The skill triggers on its own whenever a nav bar, tab bar, dock, segmented control, animated
icon, glassmorphism/blur UI, spring animation or page transition comes up — you do not have to
name it.

## Validation

```
claude plugin validate .        # official: manifest schema, naming, path safety
python3 .github/validate.py     # repo rules: skill frontmatter, dangling refs, version placement
```

Both run in CI on every push.

## Layout

```
.claude-plugin/marketplace.json     # marketplace manifest
plugins/modern-nav-motion/
  .claude-plugin/plugin.json        # plugin manifest
  skills/modern-navigation-microinteractions/
    SKILL.md
    references/*.md
.github/validate.py                 # repo-specific checks
.github/version-bumped.py           # release gate: content change requires a version bump
```

## License

MIT — see `LICENSE`.
