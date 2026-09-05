#!/usr/bin/env python3
# ==============================================================================
# 🎼 COMPOSER CORE — shared engine for the per-platform Maestros
# ==============================================================================
# Registry-agnostic pieces: colors, HTTP, threaded resolution with a curated
# offline fallback, the default stack view, and the common CLI.
#
# Platform scripts (composer_ios / web / flutter / kmp) supply three things:
#   CATALOGS        {preset: {name, description, modules: {section: [pkg, ...]}}}
#   STABLE_DEFAULTS {pkg: version}   — guarantees output with no network
#   a resolver      fn(pkg) -> (version|None, repo_label|None)
# ==============================================================================

import argparse
import concurrent.futures
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

__all__ = [
    "C", "http_get", "get_json", "latest_stable", "Resolver",
    "build_parser", "print_header", "print_stack", "print_quick_actions",
    "generate_agent_manifest", "write_out",
]

C = {
    'CYAN': '\033[96m', 'B_CYAN': '\033[1;96m',
    'GREEN': '\033[92m', 'B_GREEN': '\033[1;92m',
    'YELLOW': '\033[93m', 'B_YELLOW': '\033[1;93m',
    'MAGENTA': '\033[95m', 'B_MAGENTA': '\033[1;95m',
    'RED': '\033[91m', 'B_RED': '\033[1;91m',
    'WHITE': '\033[97m', 'B_WHITE': '\033[1;97m',
    'GRAY': '\033[90m', 'RESET': '\033[0m'
}

if not sys.stdout.isatty() or os.getenv("NO_COLOR"):
    C = {k: '' for k in C}

USER_AGENT = "Composer-Maestro/1.0"

# --- HTTP ---------------------------------------------------------------------

def http_get(url, timeout=6, accept=None):
    """Return (status, body). Never raises — a dead registry falls back to curated."""
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode('utf-8', errors='ignore')
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def get_json(url, timeout=6):
    status, body = http_get(url, timeout, accept="application/json")
    if status == 200 and body:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    return None


PRERELEASE = re.compile(r'(alpha|beta|rc|dev|snapshot|preview|nightly|[-+]pre)', re.I)


def _version_key(v):
    """Sort 1.10.0 above 1.9.0 — string sort gets this wrong, which is the whole point."""
    parts = re.findall(r'\d+', v)
    return [int(p) for p in parts[:4]] or [0]


def latest_stable(versions):
    """Newest non-prerelease version, or newest overall if every candidate is a prerelease."""
    versions = [v for v in versions if v]
    if not versions:
        return None
    stable = [v for v in versions if not PRERELEASE.search(v)]
    return max(stable or versions, key=_version_key)


# --- Resolution ---------------------------------------------------------------

class Resolver:
    """Runs a platform resolver over every package in a catalog, in parallel.

    A package that the registry cannot answer for falls back to STABLE_DEFAULTS so
    the tool still emits a complete, usable manifest offline — the fallback is
    labelled in the output rather than hidden.
    """

    def __init__(self, resolve_fn, stable_defaults, workers=10):
        self.resolve_fn = resolve_fn
        self.stable_defaults = stable_defaults
        self.workers = workers

    def _one(self, pkg):
        version = repo = None
        try:
            version, repo = self.resolve_fn(pkg)
        except Exception:
            version = None
        if not version:
            version = self.stable_defaults.get(pkg)
            repo = "Curated Stable"
        if not version:
            version = "0.0.0"
            repo = "UNRESOLVED"
        return {"pkg": pkg, "version": version, "repo": repo or "Registry"}

    def resolve_all(self, catalog_modules):
        packages = [p for deps in catalog_modules.values() for p in deps]
        out = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            for fut in concurrent.futures.as_completed(
                {ex.submit(self._one, p): p for p in packages}
            ):
                res = fut.result()
                out[res["pkg"]] = res
        return out


# --- CLI ----------------------------------------------------------------------

def build_parser(prog, description, catalogs, formats):
    """formats: [(flag, help), ...] — the platform's own output modes."""
    p = argparse.ArgumentParser(
        prog=prog, description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    presets = list(catalogs)
    p.add_argument('--app', type=str, default=presets[0], choices=presets,
                   help=f'Application domain preset (default: {presets[0]})')
    for flag, helptext in formats:
        p.add_argument(f'--{flag}', action='store_true', help=helptext)
    p.add_argument('--agent-manifest', action='store_true',
                   help='Generate JSON context for LLMs')
    p.add_argument('--offline', action='store_true',
                   help='Skip the network and use curated stable versions only')
    p.add_argument('-o', '--out', type=str, metavar='FILE',
                   help='Write generated output to FILE instead of stdout')
    return p


def print_header(title, app_data):
    bar = f"{C['B_CYAN']}============================================================={C['RESET']}"
    print(bar)
    print(f"{C['B_CYAN']} {title} {C['RESET']}")
    print(bar)
    print(f" 🎯 Active App Preset: {C['B_YELLOW']}{app_data['name']}{C['RESET']}")
    print(f" 📖 Description      : {C['GRAY']}{app_data['description']}{C['RESET']}\n")


def print_stack(catalog_modules, resolved):
    fallbacks = sum(1 for r in resolved.values() if r['repo'] in ("Curated Stable", "UNRESOLVED"))
    if fallbacks:
        print(f"{C['B_YELLOW']}⚠  {fallbacks} package(s) fell back to curated versions "
              f"(registry unreachable or unknown package).{C['RESET']}\n")
    else:
        print(f"{C['B_GREEN']}✅ All versions resolved from live registries!{C['RESET']}\n")

    width = max((len(p) for p in resolved), default=30)
    width = min(max(width, 24), 52)
    for section, packages in catalog_modules.items():
        print(f"{C['B_MAGENTA']}── {section} ──{C['RESET']}")
        for pkg in packages:
            r = resolved[pkg]
            print(f"   {C['WHITE']}{pkg:<{width}}{C['RESET']} "
                  f"v{C['B_YELLOW']}{r['version']:<12}{C['RESET']} "
                  f"[{C['GRAY']}{r['repo']}{C['RESET']}]")
        print("")


def print_quick_actions(prog, app, actions):
    print(f"{C['B_CYAN']}💡 Quick Actions for this App:{C['RESET']}")
    pad = max(len(flag) for flag, _ in actions)
    for flag, label in actions:
        print(f"  python3 {prog} --app {app} --{flag:<{pad}}   ({label})")


def generate_agent_manifest(platform, app_key, app_data, resolved):
    manifest = {
        "platform": platform,
        "preset": app_key,
        "name": app_data["name"],
        "description": app_data["description"],
        "resolved_at_versions": {p: r["version"] for p, r in sorted(resolved.items())},
        "sources": {p: r["repo"] for p, r in sorted(resolved.items())},
        "modules": {
            section: [{"package": p, "version": resolved[p]["version"]} for p in packages]
            for section, packages in app_data["modules"].items()
        },
    }
    return json.dumps(manifest, indent=2)


def write_out(text, path=None):
    if path:
        with open(path, 'w') as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
        print(f"{C['B_GREEN']}✅ Wrote {path}{C['RESET']}")
    else:
        print(text)
