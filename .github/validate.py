#!/usr/bin/env python3
"""Fail CI if the marketplace, plugin manifests, or skill frontmatter drift."""
import json, pathlib, re, sys

root = pathlib.Path(__file__).resolve().parent.parent
errors = []

market = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
for entry in market["plugins"]:
    pdir = (root / entry["source"]).resolve()
    manifest = pdir / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        errors.append(f"{entry['name']}: missing plugin.json")
        continue
    plugin = json.loads(manifest.read_text())
    if plugin["name"] != entry["name"]:
        errors.append(f"{entry['name']}: plugin.json name is {plugin['name']}")
    if plugin["version"] != entry["version"]:
        errors.append(
            f"{entry['name']}: version {plugin['version']} != marketplace {entry['version']}"
        )
    skills = sorted((pdir / "skills").glob("*/SKILL.md"))
    if not skills:
        errors.append(f"{entry['name']}: no skills/<name>/SKILL.md")
    for skill in skills:
        text = skill.read_text()
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if not m:
            errors.append(f"{skill}: missing YAML frontmatter")
            continue
        front = m.group(1)
        name = re.search(r"^name:\s*(\S+)", front, re.M)
        if not name:
            errors.append(f"{skill}: frontmatter has no name")
        elif name.group(1) != skill.parent.name:
            errors.append(f"{skill}: name {name.group(1)} != directory {skill.parent.name}")
        if not re.search(r"^description:\s*\S", front, re.M):
            errors.append(f"{skill}: frontmatter has no description")
        for ref in sorted(set(re.findall(r"references/([A-Za-z0-9_.-]+\.md)", text))):
            if not (skill.parent / "references" / ref).exists():
                errors.append(f"{skill}: references/{ref} does not exist")

for e in errors:
    print("ERROR:", e)
print("FAIL" if errors else "OK: manifests and skills validate")
sys.exit(1 if errors else 0)
