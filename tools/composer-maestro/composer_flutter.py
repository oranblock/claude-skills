#!/usr/bin/env python3
# ==============================================================================
# 🎼 COMPOSER FLUTTER MAESTRO — Dart/Flutter stack architect
# ==============================================================================
# Resolves live versions from pub.dev, emits pubspec.yaml, `flutter pub add`
# lines, or an LLM context manifest.
#
# Usage:
#   python3 composer_flutter.py --app food                  # View the stack
#   python3 composer_flutter.py --app food --pubspec        # Generate pubspec.yaml
#   python3 composer_flutter.py --app food --add            # flutter pub add lines
#   python3 composer_flutter.py --app food --agent-manifest # LLM context
# ==============================================================================

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composer_core import (C, Resolver, log, build_parser, generate_agent_manifest, get_json,
                           print_header, print_quick_actions, print_stack, write_out)

PROG = "composer_flutter.py"

CATALOGS = {
    "food": {
        "name": "🍔 Food Delivery & Restaurant Ordering (Flutter)",
        "description": "Menu browsing, cart pricing, live driver tracking, checkout & payments.",
        "modules": {
            "1. Routing & Navigation": ["go_router"],
            "2. State Management": ["flutter_riverpod", "riverpod_annotation"],
            "3. Network & Serialization": ["dio", "retrofit", "json_annotation", "freezed_annotation"],
            "4. Images & Food Visuals": ["cached_network_image", "shimmer"],
            "5. Live Map & Driver Tracking": ["google_maps_flutter", "geolocator"],
            "6. Animation & Micro-Interactions": ["lottie", "flutter_animate"],
            "7. Local Cart & Storage": ["drift", "shared_preferences"],
            "8. Payments": ["flutter_stripe"],
            "9. Codegen & Tooling": ["build_runner", "freezed", "json_serializable", "very_good_analysis"],
        },
    },
    "ecommerce": {
        "name": "🛍️ E-Commerce & Retail Marketplace (Flutter)",
        "description": "Product catalog, faceted search, wishlist, multi-currency checkout, reviews.",
        "modules": {
            "1. Routing & Navigation": ["go_router"],
            "2. State Management": ["flutter_riverpod", "riverpod_annotation"],
            "3. Network & Serialization": ["dio", "retrofit", "json_annotation", "freezed_annotation"],
            "4. Images": ["cached_network_image", "shimmer"],
            "5. Animation & Micro-Interactions": ["flutter_animate"],
            "6. Local Database & Wishlist": ["drift", "shared_preferences"],
            "7. Payments": ["flutter_stripe"],
            "8. Codegen & Tooling": ["build_runner", "freezed", "json_serializable", "very_good_analysis"],
        },
    },
    "chat": {
        "name": "💬 Realtime Chat & Messaging (Flutter)",
        "description": "Live channels, presence, typing indicators, media upload, push notifications.",
        "modules": {
            "1. Routing & Navigation": ["go_router"],
            "2. State Management": ["flutter_riverpod", "riverpod_annotation"],
            "3. Realtime Transport": ["web_socket_channel", "supabase_flutter"],
            "4. Network & Serialization": ["dio", "json_annotation", "freezed_annotation"],
            "5. Media & Attachments": ["image_picker", "cached_network_image"],
            "6. Animation & Micro-Interactions": ["flutter_animate"],
            "7. Local Cache": ["drift", "shared_preferences"],
            "8. Push Notifications": ["firebase_messaging"],
            "9. Codegen & Tooling": ["build_runner", "freezed", "json_serializable", "very_good_analysis"],
        },
    },
    "standard": {
        "name": "🧱 Standard Flutter App Baseline",
        "description": "The unopinionated starting point: routing, state, network, storage, lints.",
        "modules": {
            "1. Routing & Navigation": ["go_router"],
            "2. State Management": ["flutter_riverpod"],
            "3. Network & Serialization": ["dio", "json_annotation"],
            "4. Images": ["cached_network_image"],
            "5. Local Storage": ["shared_preferences"],
            "6. Codegen & Tooling": ["build_runner", "json_serializable", "very_good_analysis"],
        },
    },
}

DEV_PACKAGES = {"build_runner", "freezed", "json_serializable", "very_good_analysis",
                "riverpod_annotation", "retrofit_generator", "drift_dev"}

STABLE_DEFAULTS = {
    "go_router": "14.6.3", "flutter_riverpod": "2.6.1", "riverpod_annotation": "2.6.1",
    "dio": "5.7.0", "retrofit": "4.4.2", "json_annotation": "4.9.0",
    "freezed_annotation": "2.4.4", "cached_network_image": "3.4.1", "shimmer": "3.0.0",
    "google_maps_flutter": "2.10.0", "geolocator": "13.0.2",
    "lottie": "3.3.1", "flutter_animate": "4.5.2",
    "drift": "2.23.1", "shared_preferences": "2.3.5",
    "flutter_stripe": "11.3.0", "web_socket_channel": "3.0.2",
    "supabase_flutter": "2.8.3", "image_picker": "1.1.2", "firebase_messaging": "15.1.6",
    "build_runner": "2.4.14", "freezed": "2.5.8", "json_serializable": "6.9.3",
    "very_good_analysis": "6.0.0",
}


def resolve_pub(pkg):
    """pub.dev reports the resolved latest under 'latest.version'."""
    data = get_json(f"https://pub.dev/api/packages/{pkg}")
    if not data:
        return None, None
    version = (data.get("latest") or {}).get("version")
    return (version, "pub.dev") if version else (None, None)


def _caret(version):
    return f"^{version}"


def generate_pubspec(app_key, app_data, resolved):
    deps, dev = [], []
    for packages in app_data["modules"].values():
        for pkg in packages:
            (dev if pkg in DEV_PACKAGES else deps).append(pkg)

    lines = [
        f"name: {app_key}_app",
        f"description: {app_data['description']}",
        "publish_to: 'none'",
        "version: 0.1.0+1",
        "",
        "environment:",
        "  sdk: '>=3.5.0 <4.0.0'",
        "  flutter: '>=3.27.0'",
        "",
        "dependencies:",
        "  flutter:",
        "    sdk: flutter",
    ]
    for pkg in sorted(set(deps)):
        lines.append(f"  {pkg}: {_caret(resolved[pkg]['version'])}")
    lines += ["", "dev_dependencies:", "  flutter_test:", "    sdk: flutter"]
    for pkg in sorted(set(dev)):
        lines.append(f"  {pkg}: {_caret(resolved[pkg]['version'])}")
    lines += ["", "flutter:", "  uses-material-design: true"]
    return "\n".join(lines)


def generate_add(app_data, resolved):
    deps, dev = [], []
    for packages in app_data["modules"].values():
        for pkg in packages:
            (dev if pkg in DEV_PACKAGES else deps).append(f"{pkg}:^{resolved[pkg]['version']}")
    return "\n".join([
        "flutter pub add " + " ".join(sorted(set(deps))),
        "flutter pub add --dev " + " ".join(sorted(set(dev))),
    ])


def main():
    parser = build_parser(
        PROG, "🎼 Composer Flutter Maestro — Dart/Flutter stack architect", CATALOGS,
        [("pubspec", "Output pubspec.yaml"), ("add", "Output flutter pub add commands")],
    )
    args = parser.parse_args()
    app_data = CATALOGS[args.app]

    print_header("🎼 COMPOSER FLUTTER MAESTRO (v1.0)", app_data)

    if args.offline:
        log(f"{C['GRAY']}📴 Offline mode — using curated stable versions.{C['RESET']}")
        resolver = Resolver(lambda pkg: (None, None), STABLE_DEFAULTS)
    else:
        log(f"{C['GRAY']}📡 Contacting pub.dev for live versions...{C['RESET']}")
        resolver = Resolver(resolve_pub, STABLE_DEFAULTS)
    resolved = resolver.resolve_all(app_data["modules"])

    if args.pubspec:
        write_out(generate_pubspec(args.app, app_data, resolved), args.out)
    elif args.add:
        write_out(generate_add(app_data, resolved), args.out)
    elif args.agent_manifest:
        write_out(generate_agent_manifest("flutter", args.app, app_data, resolved), args.out)
    else:
        log("")
        print_stack(app_data["modules"], resolved)
        print_quick_actions(PROG, args.app, [
            ("pubspec", "Generate pubspec.yaml"),
            ("add", "Generate pub add commands"),
            ("agent-manifest", "Generate AI context"),
        ])


if __name__ == "__main__":
    main()
