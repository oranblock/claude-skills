#!/usr/bin/env python3
"""Because plugin.json pins a version, installs only update when that version changes.
Fail the build if plugin content changed without a bump. Runs on pushes as well as PRs —
on a solo repo the push path is the only path that ever fires."""
import json, pathlib, subprocess, sys

root = pathlib.Path(__file__).resolve().parent.parent

def resolve(ref):
    """Return ref if git can resolve it to a commit, else None."""
    if not ref or set(ref) <= {"0"}:  # GitHub sends an all-zero SHA for a new branch
        return None
    ok = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=root, capture_output=True, text=True,
    )
    return ref if ok.returncode == 0 else None


base = resolve(sys.argv[1] if len(sys.argv) > 1 else None) or resolve("HEAD^")
if base is None:
    print("SKIP: no resolvable base commit to diff against")
    sys.exit(0)
print(f"Comparing against {base}")

market = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
failed = False

for entry in market.get("plugins", []):
    source = entry["source"].removeprefix("./")
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
        print(f"OK: {entry['name']} is new at {base}")
        continue
    before = json.loads(old.stdout).get("version")
    after = json.loads((root / manifest).read_text()).get("version")
    if before == after:
        print(f"ERROR: {entry['name']} changed ({len(changed)} files) but version is still {after}")
        failed = True
    else:
        print(f"OK: {entry['name']} {before} -> {after}")

sys.exit(1 if failed else 0)
