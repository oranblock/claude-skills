# oranblock-skills — a Claude Code plugin marketplace

Install skills the same way you install anything else in Claude Code: add the marketplace once,
install the plugin, and Claude Code keeps it up to date from this repo.

## Install

```
/plugin marketplace add oranblock/claude-skills
/plugin install modern-nav-motion@oranblock-skills
```

Then restart Claude Code (or run `/plugin`) and the skill is live in every project.

## Staying on the latest version

Claude Code refreshes marketplaces it has added from git, so a push here reaches installs
without any manual step. To force it immediately:

```
/plugin marketplace update oranblock-skills
```

`/plugin` → *Manage marketplaces* shows the currently installed version against this repo's.

## Plugins

### `modern-nav-motion` (v1.1.0)

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

## Layout

```
.claude-plugin/marketplace.json     # marketplace manifest
plugins/modern-nav-motion/
  .claude-plugin/plugin.json        # plugin manifest
  skills/modern-navigation-microinteractions/
    SKILL.md
    references/*.md
```

## License

MIT — see `LICENSE`.
