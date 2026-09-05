#!/usr/bin/env python3
# ==============================================================================
# 🎼 COMPOSER iOS MAESTRO — SwiftUI / Swift Package Manager stack architect
# ==============================================================================
# Resolves live versions from GitHub release tags (which is where SPM actually
# reads versions from), emits Package.swift, an Xcode add-package checklist, or
# an LLM context manifest.
#
# Packages are identified by their GitHub "owner/repo", because that is the SPM
# identity — not a registry name.
#
# Usage:
#   python3 composer_ios.py --app food                   # View the stack
#   python3 composer_ios.py --app food --package         # Generate Package.swift
#   python3 composer_ios.py --app food --xcode           # Xcode add-package list
#   python3 composer_ios.py --app food --agent-manifest  # LLM context
#
# Note: unauthenticated GitHub API allows ~60 requests/hour. Set GITHUB_TOKEN to
# raise it; without one, rate-limited packages fall back to curated versions and
# are labelled as such in the output.
# ==============================================================================

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composer_core import (C, Resolver, build_parser, generate_agent_manifest, get_json,
                           http_get, latest_stable, print_header, print_quick_actions,
                           print_stack, write_out)

PROG = "composer_ios.py"

CATALOGS = {
    "food": {
        "name": "🍔 Food Delivery & Restaurant Ordering (SwiftUI)",
        "description": "Menu browsing, cart pricing, live driver tracking, checkout & payments.",
        "modules": {
            "1. Networking & API": ["Alamofire/Alamofire", "apple/swift-http-types"],
            "2. Async Images & Food Visuals": ["kean/Nuke", "onevcat/Kingfisher"],
            "3. Dependency Injection & Architecture": [
                "pointfreeco/swift-composable-architecture", "pointfreeco/swift-dependencies",
            ],
            "4. Local Cart & Persistence": ["groue/GRDB.swift", "realm/realm-swift"],
            "5. Animation & Micro-Interactions": ["airbnb/lottie-ios"],
            "6. Maps & Driver Tracking": ["maplibre/maplibre-gl-native-distribution"],
            "7. Payments": ["stripe/stripe-ios"],
            "8. Testing & Quality": ["pointfreeco/swift-snapshot-testing", "realm/SwiftLint"],
        },
    },
    "ecommerce": {
        "name": "🛍️ E-Commerce & Retail Marketplace (SwiftUI)",
        "description": "Product catalog, faceted search, wishlist, multi-currency checkout, reviews.",
        "modules": {
            "1. Networking & API": ["Alamofire/Alamofire"],
            "2. Async Images": ["kean/Nuke", "onevcat/Kingfisher"],
            "3. Architecture & State": [
                "pointfreeco/swift-composable-architecture", "pointfreeco/swift-dependencies",
            ],
            "4. Local Database & Wishlist": ["groue/GRDB.swift"],
            "5. Animation & Micro-Interactions": ["airbnb/lottie-ios"],
            "6. Payments": ["stripe/stripe-ios"],
            "7. Testing & Quality": ["pointfreeco/swift-snapshot-testing", "realm/SwiftLint"],
        },
    },
    "chat": {
        "name": "💬 Realtime Chat & Messaging (SwiftUI)",
        "description": "Live channels, presence, typing indicators, media upload, push notifications.",
        "modules": {
            "1. Realtime Transport": ["daltoniam/Starscream", "supabase/supabase-swift"],
            "2. Networking & API": ["Alamofire/Alamofire"],
            "3. Architecture & State": ["pointfreeco/swift-composable-architecture"],
            "4. Async Images & Attachments": ["kean/Nuke"],
            "5. Local Cache": ["groue/GRDB.swift"],
            "6. Animation & Micro-Interactions": ["airbnb/lottie-ios"],
            "7. Testing & Quality": ["pointfreeco/swift-snapshot-testing", "realm/SwiftLint"],
        },
    },
    "standard": {
        "name": "🧱 Standard SwiftUI App Baseline",
        "description": "The unopinionated starting point: networking, images, state, storage, lint.",
        "modules": {
            "1. Networking & API": ["Alamofire/Alamofire"],
            "2. Async Images": ["kean/Nuke"],
            "3. Architecture & State": ["pointfreeco/swift-dependencies"],
            "4. Persistence": ["groue/GRDB.swift"],
            "5. Testing & Quality": ["pointfreeco/swift-snapshot-testing", "realm/SwiftLint"],
        },
    },
}

# repo -> the library product name you actually write in a target's dependencies.
PRODUCTS = {
    "Alamofire/Alamofire": ["Alamofire"],
    "apple/swift-http-types": ["HTTPTypes"],
    "kean/Nuke": ["Nuke", "NukeUI"],
    "onevcat/Kingfisher": ["Kingfisher"],
    "pointfreeco/swift-composable-architecture": ["ComposableArchitecture"],
    "pointfreeco/swift-dependencies": ["Dependencies"],
    "groue/GRDB.swift": ["GRDB"],
    "realm/realm-swift": ["RealmSwift"],
    "airbnb/lottie-ios": ["Lottie"],
    "maplibre/maplibre-gl-native-distribution": ["MapLibre"],
    "stripe/stripe-ios": ["StripePaymentSheet"],
    "daltoniam/Starscream": ["Starscream"],
    "supabase/supabase-swift": ["Supabase"],
    "pointfreeco/swift-snapshot-testing": ["SnapshotTesting"],
}

TEST_ONLY = {"pointfreeco/swift-snapshot-testing"}

# SwiftLint attaches as a build-tool plugin, not as a linkable product.
PLUGINS = {"realm/SwiftLint": "SwiftLintBuildToolPlugin"}

STABLE_DEFAULTS = {
    "Alamofire/Alamofire": "5.10.2", "apple/swift-http-types": "1.3.1",
    "kean/Nuke": "12.8.0", "onevcat/Kingfisher": "8.1.3",
    "pointfreeco/swift-composable-architecture": "1.17.0",
    "pointfreeco/swift-dependencies": "1.6.3",
    "groue/GRDB.swift": "7.1.0", "realm/realm-swift": "20.0.0",
    "airbnb/lottie-ios": "4.5.1",
    "maplibre/maplibre-gl-native-distribution": "6.9.0",
    "stripe/stripe-ios": "24.5.0", "daltoniam/Starscream": "4.0.8",
    "supabase/supabase-swift": "2.24.0",
    "pointfreeco/swift-snapshot-testing": "1.18.1", "realm/SwiftLint": "0.57.1",
}


def resolve_github_tag(repo):
    """SPM resolves versions from git tags, so that is what we read."""
    token = os.getenv("GITHUB_TOKEN")
    url = f"https://api.github.com/repos/{repo}/tags?per_page=100"
    if token:
        import urllib.request
        req = urllib.request.Request(
            url, headers={"User-Agent": "Composer-Maestro/1.0",
                          "Authorization": f"Bearer {token}",
                          "Accept": "application/vnd.github+json"})
        try:
            import json as _json
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = _json.loads(resp.read().decode("utf-8", "ignore"))
        except Exception:
            data = None
    else:
        data = get_json(url)

    if not isinstance(data, list) or not data:
        return None, None
    names = [t.get("name", "").lstrip("v") for t in data if t.get("name")]
    # Keep semver-shaped tags only; repos also tag things like "swift-5" or "old-api".
    names = [n for n in names if n and n[0].isdigit() and "." in n]
    picked = latest_stable(names)
    return (picked, "GitHub") if picked else (None, None)


def generate_package_swift(app_key, app_data, resolved):
    repos = [r for packages in app_data["modules"].values() for r in packages]
    app_deps = [r for r in repos if r not in TEST_ONLY and r not in PLUGINS]
    test_deps = [r for r in repos if r in TEST_ONLY]
    plugin_deps = [r for r in repos if r in PLUGINS]

    def dep_line(repo):
        return (f'        .package(url: "https://github.com/{repo}.git", '
                f'from: "{resolved[repo]["version"]}"),')

    def product_lines(repo_list, indent="            "):
        out = []
        for repo in repo_list:
            owner_repo = repo.split("/")[-1]
            for product in PRODUCTS.get(repo, [owner_repo]):
                out.append(f'{indent}.product(name: "{product}", package: "{owner_repo}"),')
        return out

    name = f"{app_key.capitalize()}App"
    lines = [
        "// swift-tools-version: 6.0",
        f"// {app_data['name']}",
        "import PackageDescription",
        "",
        "let package = Package(",
        f'    name: "{name}",',
        "    platforms: [.iOS(.v17)],",
        "    products: [",
        f'        .library(name: "{name}", targets: ["{name}"]),',
        "    ],",
        "    dependencies: [",
    ]
    lines += [dep_line(r) for r in app_deps + test_deps + plugin_deps]
    lines += [
        "    ],",
        "    targets: [",
        "        .target(",
        f'            name: "{name}",',
        "            dependencies: [",
    ]
    lines += product_lines(app_deps)
    lines += ["            ]"]
    if plugin_deps:
        lines.append("            ,plugins: [")
        for repo in plugin_deps:
            lines.append(f'                .plugin(name: "{PLUGINS[repo]}", '
                         f'package: "{repo.split("/")[-1]}"),')
        lines.append("            ]")
    lines += [
        "        ),",
        "        .testTarget(",
        f'            name: "{name}Tests",',
        f'            dependencies: ["{name}",',
    ]
    lines += product_lines(test_deps, indent="                          ")
    lines += [
        "            ]",
        "        ),",
        "    ]",
        ")",
    ]
    return "\n".join(lines)


def generate_xcode(app_data, resolved):
    lines = ["# Xcode ▸ File ▸ Add Package Dependencies… — paste each URL, pick 'Up to Next Major'",
             ""]
    for section, repos in app_data["modules"].items():
        lines.append(f"## {section}")
        for repo in repos:
            if repo in PLUGINS:
                products = f"build-tool plugin {PLUGINS[repo]}"
            else:
                products = ", ".join(PRODUCTS.get(repo, [repo.split('/')[-1]]))
            lines.append(f"  https://github.com/{repo}.git"
                         f"   from {resolved[repo]['version']}   → add: {products}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = build_parser(
        PROG, "🎼 Composer iOS Maestro — SwiftUI/SPM stack architect", CATALOGS,
        [("package", "Output Package.swift"), ("xcode", "Output Xcode add-package checklist")],
    )
    args = parser.parse_args()
    app_data = CATALOGS[args.app]

    print_header("🎼 COMPOSER iOS MAESTRO (v1.0)", app_data)

    if args.offline:
        print(f"{C['GRAY']}📴 Offline mode — using curated stable versions.{C['RESET']}")
        resolver = Resolver(lambda pkg: (None, None), STABLE_DEFAULTS)
    else:
        if not os.getenv("GITHUB_TOKEN"):
            print(f"{C['GRAY']}💡 No GITHUB_TOKEN set — GitHub allows ~60 requests/hour "
                  f"unauthenticated.{C['RESET']}")
        print(f"{C['GRAY']}📡 Reading release tags from GitHub...{C['RESET']}")
        resolver = Resolver(resolve_github_tag, STABLE_DEFAULTS, workers=6)
    resolved = resolver.resolve_all(app_data["modules"])

    if args.package:
        write_out(generate_package_swift(args.app, app_data, resolved), args.out)
    elif args.xcode:
        write_out(generate_xcode(app_data, resolved), args.out)
    elif args.agent_manifest:
        write_out(generate_agent_manifest("ios", args.app, app_data, resolved), args.out)
    else:
        print("")
        print_stack(app_data["modules"], resolved)
        print_quick_actions(PROG, args.app, [
            ("package", "Generate Package.swift"),
            ("xcode", "Generate Xcode checklist"),
            ("agent-manifest", "Generate AI context"),
        ])


if __name__ == "__main__":
    main()
