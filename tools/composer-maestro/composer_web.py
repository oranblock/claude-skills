#!/usr/bin/env python3
# ==============================================================================
# 🎼 COMPOSER WEB MAESTRO — React / Next.js stack architect
# ==============================================================================
# Resolves live versions from the npm registry, emits package.json, an install
# command, or an LLM context manifest.
#
# Usage:
#   python3 composer_web.py --app food                     # View the stack
#   python3 composer_web.py --app food --pkg               # Generate package.json
#   python3 composer_web.py --app food --install           # npm/pnpm install line
#   python3 composer_web.py --app food --agent-manifest    # LLM context
#   python3 composer_web.py --app food --pkg -o package.json
# ==============================================================================

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composer_core import (C, Resolver, log, build_parser, generate_agent_manifest, get_json,
                           latest_stable, print_header, print_quick_actions, print_stack,
                           write_out)

PROG = "composer_web.py"

# ==============================================================================
# 📚 APPLICATION PRESET STACKS
# ==============================================================================

CATALOGS = {
    "food": {
        "name": "🍔 Food Delivery & Restaurant Ordering (Next.js)",
        "description": "Menu browsing, cart pricing, live driver tracking on a map, checkout & payments.",
        "modules": {
            "1. Framework & React Core": ["next", "react", "react-dom"],
            "2. Routing, Data & Server State": ["@tanstack/react-query", "zod"],
            "3. Client State": ["zustand"],
            "4. Styling & UI Primitives": [
                "tailwindcss", "clsx", "tailwind-merge",
                "@radix-ui/react-dialog", "lucide-react",
            ],
            "5. Animation & Micro-Interactions": ["motion"],
            "6. Live Map & Driver Tracking": ["maplibre-gl", "react-map-gl"],
            "7. Forms & Validation": ["react-hook-form", "@hookform/resolvers"],
            "8. Payments": ["@stripe/stripe-js"],
            "9. Tooling": ["typescript", "eslint", "vitest"],
        },
    },
    "ecommerce": {
        "name": "🛍️ E-Commerce & Retail Marketplace (Next.js)",
        "description": "Product catalog, faceted search, cart, multi-currency checkout, reviews.",
        "modules": {
            "1. Framework & React Core": ["next", "react", "react-dom"],
            "2. Data & Server State": ["@tanstack/react-query", "zod"],
            "3. Client State": ["zustand"],
            "4. Styling & UI Primitives": [
                "tailwindcss", "clsx", "tailwind-merge",
                "@radix-ui/react-dialog", "lucide-react",
            ],
            "5. Animation & Micro-Interactions": ["motion"],
            "6. Search & Filtering": ["fuse.js"],
            "7. Forms & Validation": ["react-hook-form", "@hookform/resolvers"],
            "8. Payments": ["@stripe/stripe-js"],
            "9. Tooling": ["typescript", "eslint", "vitest"],
        },
    },
    "chat": {
        "name": "💬 Realtime Chat & Messaging (Next.js)",
        "description": "Live channels, presence, typing indicators, optimistic sends, media upload.",
        "modules": {
            "1. Framework & React Core": ["next", "react", "react-dom"],
            "2. Realtime Transport": ["socket.io-client", "@supabase/supabase-js"],
            "3. Data & Server State": ["@tanstack/react-query", "zod"],
            "4. Client State": ["zustand"],
            "5. Styling & UI Primitives": [
                "tailwindcss", "clsx", "tailwind-merge", "lucide-react",
            ],
            "6. Animation & Micro-Interactions": ["motion"],
            "7. Virtualised Message List": ["@tanstack/react-virtual"],
            "8. Tooling": ["typescript", "eslint", "vitest"],
        },
    },
    "standard": {
        "name": "🧱 Standard Web App Baseline (Next.js)",
        "description": "The unopinionated starting point: routing, data, styling, forms, tests.",
        "modules": {
            "1. Framework & React Core": ["next", "react", "react-dom"],
            "2. Data & Server State": ["@tanstack/react-query", "zod"],
            "3. Client State": ["zustand"],
            "4. Styling & UI Primitives": ["tailwindcss", "clsx", "tailwind-merge", "lucide-react"],
            "5. Animation": ["motion"],
            "6. Forms & Validation": ["react-hook-form", "@hookform/resolvers"],
            "7. Tooling": ["typescript", "eslint", "vitest"],
        },
    },
}

# Packages that belong in devDependencies, not dependencies.
DEV_PACKAGES = {"typescript", "eslint", "vitest", "tailwindcss"}

# Curated fallbacks — used when the registry is unreachable.
STABLE_DEFAULTS = {
    "next": "15.1.6", "react": "19.0.0", "react-dom": "19.0.0",
    "@tanstack/react-query": "5.66.0", "@tanstack/react-virtual": "3.11.2",
    "zod": "3.24.1", "zustand": "5.0.3",
    "tailwindcss": "3.4.17", "clsx": "2.1.1", "tailwind-merge": "2.6.0",
    "@radix-ui/react-dialog": "1.1.5", "lucide-react": "0.474.0",
    "motion": "11.18.2",
    "maplibre-gl": "5.1.0", "react-map-gl": "7.1.8",
    "react-hook-form": "7.54.2", "@hookform/resolvers": "3.10.0",
    "@stripe/stripe-js": "5.5.0",
    "socket.io-client": "4.8.1", "@supabase/supabase-js": "2.48.1",
    "fuse.js": "7.0.0",
    "typescript": "5.7.3", "eslint": "9.19.0", "vitest": "3.0.4",
}

# ==============================================================================
# 🌐 RESOLUTION — npm registry
# ==============================================================================

def resolve_npm(pkg):
    """Ask the registry for dist-tags.latest, ignoring prereleases published as 'next'."""
    data = get_json(f"https://registry.npmjs.org/{pkg.replace('/', '%2F')}")
    if not data:
        return None, None
    latest = (data.get("dist-tags") or {}).get("latest")
    if latest:
        return latest, "npm"
    versions = list((data.get("versions") or {}).keys())
    picked = latest_stable(versions)
    return (picked, "npm") if picked else (None, None)


# ==============================================================================
# 📝 OUTPUT GENERATORS
# ==============================================================================

def generate_package_json(app_key, app_data, resolved):
    deps, dev = {}, {}
    for packages in app_data["modules"].values():
        for pkg in packages:
            target = dev if pkg in DEV_PACKAGES else deps
            target[pkg] = f"^{resolved[pkg]['version']}"
    manifest = {
        "name": f"{app_key}-app",
        "version": "0.1.0",
        "private": True,
        "type": "module",
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "eslint .",
            "test": "vitest run",
        },
        "dependencies": dict(sorted(deps.items())),
        "devDependencies": dict(sorted(dev.items())),
    }
    return json.dumps(manifest, indent=2)


def generate_install(app_data, resolved):
    deps, dev = [], []
    for packages in app_data["modules"].values():
        for pkg in packages:
            spec = f"{pkg}@{resolved[pkg]['version']}"
            (dev if pkg in DEV_PACKAGES else deps).append(spec)
    lines = [
        "# npm",
        "npm install " + " ".join(sorted(deps)),
        "npm install -D " + " ".join(sorted(dev)),
        "",
        "# pnpm",
        "pnpm add " + " ".join(sorted(deps)),
        "pnpm add -D " + " ".join(sorted(dev)),
    ]
    return "\n".join(lines)


def main():
    parser = build_parser(
        PROG, "🎼 Composer Web Maestro — Next.js/React stack architect", CATALOGS,
        [("pkg", "Output package.json"), ("install", "Output npm/pnpm install commands")],
    )
    args = parser.parse_args()
    app_data = CATALOGS[args.app]

    print_header("🎼 COMPOSER WEB MAESTRO (v1.0)", app_data)

    if args.offline:
        log(f"{C['GRAY']}📴 Offline mode — using curated stable versions.{C['RESET']}")
        resolver = Resolver(lambda pkg: (None, None), STABLE_DEFAULTS)
    else:
        log(f"{C['GRAY']}📡 Contacting the npm registry for live versions...{C['RESET']}")
        resolver = Resolver(resolve_npm, STABLE_DEFAULTS)
    resolved = resolver.resolve_all(app_data["modules"])

    if args.pkg:
        write_out(generate_package_json(args.app, app_data, resolved), args.out)
    elif args.install:
        write_out(generate_install(app_data, resolved), args.out)
    elif args.agent_manifest:
        write_out(generate_agent_manifest("web", args.app, app_data, resolved), args.out)
    else:
        log("")
        print_stack(app_data["modules"], resolved)
        print_quick_actions(PROG, args.app, [
            ("pkg", "Generate package.json"),
            ("install", "Generate install commands"),
            ("agent-manifest", "Generate AI context"),
        ])


if __name__ == "__main__":
    main()
