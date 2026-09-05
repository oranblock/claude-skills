#!/usr/bin/env python3
"""Repo-specific checks. `claude plugin validate` owns manifest schema and naming rules;
this covers what it does not: skill frontmatter/dir agreement, dangling reference links,
and our own rule that versions live in plugin.json only."""
import json, pathlib, re, sys

root = pathlib.Path(__file__).resolve().parent.parent
errors = []


def load(path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        errors.append(f"{path.relative_to(root)}: missing")
    except json.JSONDecodeError as exc:
        errors.append(f"{path.relative_to(root)}: invalid JSON ({exc})")
    return None


market = load(root / ".claude-plugin" / "marketplace.json") or {}
if not market.get("description"):
    errors.append("marketplace.json: no top-level description")

entries = market.get("plugins")
if not isinstance(entries, list) or not entries:
    errors.append("marketplace.json: no plugins list")
    entries = []

for entry in entries:
    name = entry.get("name")
    source = entry.get("source")
    if not name or not isinstance(source, str):
        errors.append(f"marketplace.json: entry {entry!r} needs a name and a string source")
        continue
    if "version" in entry:
        # Claude Code always reads plugin.json's version; a second one here can only drift.
        errors.append(f"{name}: drop 'version' from the marketplace entry, it is ignored")

    pdir = (root / source).resolve()
    plugin = load(pdir / ".claude-plugin" / "plugin.json")
    if plugin is None:
        continue
    if plugin.get("name") != name:
        errors.append(f"{name}: plugin.json name is {plugin.get('name')!r}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(plugin.get("version", ""))):
        errors.append(f"{name}: plugin.json needs a semver 'version' (updates are gated on it)")

    skills = sorted((pdir / "skills").glob("*/SKILL.md"))
    if not skills:
        errors.append(f"{name}: no skills/<name>/SKILL.md")
    for skill in skills:
        rel = skill.relative_to(root)
        text = skill.read_text()
        front = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if not front:
            errors.append(f"{rel}: missing YAML frontmatter")
            continue
        head = front.group(1)
        declared = re.search(r"^name:\s*(\S+)", head, re.M)
        if not declared:
            errors.append(f"{rel}: frontmatter has no name")
        elif declared.group(1) != skill.parent.name:
            errors.append(f"{rel}: name {declared.group(1)} != directory {skill.parent.name}")
        if not re.search(r"^description:\s*\S", head, re.M):
            errors.append(f"{rel}: frontmatter has no description")
        for ref in sorted(set(re.findall(r"references/([A-Za-z0-9_.-]+\.md)", text))):
            if not (skill.parent / "references" / ref).exists():
                errors.append(f"{rel}: references/{ref} does not exist")

for e in errors:
    print("ERROR:", e)
print("FAIL" if errors else "OK: manifests and skills validate")
sys.exit(1 if errors else 0)
