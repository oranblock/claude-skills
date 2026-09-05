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
installed. So every release bumps it, and CI fails **any push or PR** that edits plugin content
without a bump (`.github/version-bumped.py`). The push path is what actually fires on this repo,
since commits land on `main` directly.

To pull the newest version:

```
/plugin marketplace update oranblock-skills
```

`/plugin` → *Manage marketplaces* shows your installed version against this repo's.

Versions are declared in `plugin.json` only. The marketplace entry deliberately has no
`version`: Claude Code always reads `plugin.json`'s value, so a second copy here could only
drift — the validator rejects one if it reappears.

## Plugins

### `modern-nav-motion` (v1.1.2)

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

The skill triggers on its own whenever a nav bar, tab bar, dock, sidebar, segmented control, animated
icon, glassmorphism/blur UI, spring animation or page transition comes up — you do not have to
name it.

## Antigravity / Gemini CLI Support

This repository is ready out-of-the-box for **Google Antigravity (`agy`)** and **Gemini CLI**:

- **Automatic Discovery**: `.agents/skills.json` and `.agents/plugins.json` configure declared workspace entries.
- **Direct Skill Root**: `.agents/skills/modern-navigation-microinteractions` provides standard filesystem skill discovery.
- **Dual Manifests**: `plugins/modern-nav-motion/` includes both `plugin.json` (for Antigravity) and `.claude-plugin/plugin.json` (for Claude Code).

## Validation

```
claude plugin validate .                      # marketplace schema, naming, source path safety
claude plugin validate plugins/modern-nav-motion   # parses the skill/agent/command files
python3 .github/validate.py                   # repo rules: dir/name agreement, dangling refs
python3 .github/version-bumped.py             # release gate
```

All four run in CI on every push. Both `claude plugin validate` runs are needed — from the
marketplace root it only reaches the manifests, so the per-plugin run is what actually parses
`SKILL.md` frontmatter. CI pins the Claude Code version (`CLAUDE_CODE_VERSION` in the workflow)
so an upstream release cannot redden an untouched repo; bump it deliberately.

## Also in this repo

`tools/composer-maestro/` — standalone CLI dependency-stack architects for Android, KMP, iOS,
Web and Flutter. They resolve live versions from each platform's registry and emit
`package.json`, `pubspec.yaml`, `Package.swift`, `build.gradle.kts` or a version catalog. Not
plugins and not installed by `/plugin`; see `tools/composer-maestro/README.md`.

## Layout

```
tools/composer-maestro/             # standalone CLIs, not part of the marketplace
.claude-plugin/marketplace.json     # marketplace manifest (Claude Code)
.agents/                            # workspace customizations (Antigravity / Gemini CLI)
  skills.json                       # declared skills config
  plugins.json                      # declared plugins config
  skills/                           # discovered skills directory
AGENTS.md                           # AI pair programming guidelines & rules
plugins/modern-nav-motion/
  plugin.json                       # plugin manifest (Antigravity)
  .claude-plugin/plugin.json        # plugin manifest (Claude Code)
  skills/modern-navigation-microinteractions/
    SKILL.md
    references/*.md
.github/validate.py                 # repo-specific checks
.github/version-bumped.py           # release gate: content change requires a version bump
```

## Contributors

- **oranblock** ([@oranblock](https://github.com/oranblock)) — Project Author & Maintainer
- **Antigravity** ([Google DeepMind](https://deepmind.google)) — AI Pair Programmer (cross-platform stream architecture, test harnesses, Antigravity & Gemini CLI native integration)

## License

MIT — see `LICENSE`.
