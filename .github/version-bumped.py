#!/usr/bin/env python3
"""Because plugin.json pins a version, installs only update when that version changes.
Fail the PR if plugin content changed without a bump."""
import json, pathlib, subprocess, sys

root = pathlib.Path(__file__).resolve().parent.parent
base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
market = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
failed = False

for entry in market.get("plugins", []):
    source = entry["source"].lstrip("./")
    changed = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD", "--", source],
        cwd=root, capture_output=True, text=True,
    ).stdout.split()
    if not changed:
        continue
    manifest = f"{source}/.claude-plugin/plugin.json"
    old = subprocess.run(
        ["git", "show", f"{base}:{manifest}"], cwd=root, capture_output=True, text=True
    )
    if old.returncode != 0:
        continue  # new plugin
    before = json.loads(old.stdout).get("version")
    after = json.loads((root / manifest).read_text()).get("version")
    if before == after:
        print(f"ERROR: {entry['name']} changed ({len(changed)} files) but version is still {after}")
        failed = True
    else:
        print(f"OK: {entry['name']} {before} -> {after}")

sys.exit(1 if failed else 0)
