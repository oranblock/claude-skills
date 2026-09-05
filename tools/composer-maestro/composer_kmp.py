#!/usr/bin/env python3
# ==============================================================================
# 🎼 COMPOSER KMP MAESTRO — Kotlin Multiplatform / Compose Multiplatform architect
# ==============================================================================
# Resolves live versions from Maven Central and Google Maven, emits a version
# catalog, a multiplatform build.gradle.kts with real sourceSets, or an LLM
# context manifest.
#
# Usage:
#   python3 composer_kmp.py --app food                   # View the stack
#   python3 composer_kmp.py --app food --toml            # Generate libs.versions.toml
#   python3 composer_kmp.py --app food --dsl             # Generate build.gradle.kts
#   python3 composer_kmp.py --app food --agent-manifest  # LLM context
# ==============================================================================

import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composer_core import (C, Resolver, log, build_parser, generate_agent_manifest, get_json,
                           http_get, latest_stable, print_header, print_quick_actions,
                           print_stack, write_out)

PROG = "composer_kmp.py"

# Each entry: "group:artifact" tagged with the source set it belongs in.
COMMON, ANDROID, IOS = "common", "android", "ios"

CATALOGS = {
    "food": {
        "name": "🍔 Food Delivery & Restaurant Ordering (Compose Multiplatform)",
        "description": "Shared menu/cart/pricing logic, per-platform maps and payments.",
        "modules": {
            "1. Compose Multiplatform UI": [
                "org.jetbrains.compose.runtime:runtime",
                "org.jetbrains.compose.material3:material3",
                "org.jetbrains.androidx.navigation:navigation-compose",
            ],
            "2. Networking (Ktor)": [
                "io.ktor:ktor-client-core",
                "io.ktor:ktor-client-content-negotiation",
                "io.ktor:ktor-serialization-kotlinx-json",
                "io.ktor:ktor-client-okhttp",
                "io.ktor:ktor-client-darwin",
            ],
            "3. Dependency Injection (Koin)": [
                "io.insert-koin:koin-core",
                "io.insert-koin:koin-compose",
            ],
            "4. Async & Serialization": [
                "org.jetbrains.kotlinx:kotlinx-coroutines-core",
                "org.jetbrains.kotlinx:kotlinx-serialization-json",
                "org.jetbrains.kotlinx:kotlinx-datetime",
            ],
            "5. Images": ["io.coil-kt.coil3:coil-compose", "io.coil-kt.coil3:coil-network-ktor3"],
            "6. Shared Local Cart & Storage": [
                "app.cash.sqldelight:runtime",
                "app.cash.sqldelight:coroutines-extensions",
                "com.russhwolf:multiplatform-settings",
            ],
            "7. Android-only (Maps, Activity)": [
                "androidx.activity:activity-compose",
                "com.google.maps.android:maps-compose",
                "com.google.android.gms:play-services-location",
            ],
            "8. Testing": ["org.jetbrains.kotlin:kotlin-test", "app.cash.turbine:turbine"],
        },
    },
    "ecommerce": {
        "name": "🛍️ E-Commerce & Retail Marketplace (Compose Multiplatform)",
        "description": "Shared catalog, cart and checkout logic across Android and iOS.",
        "modules": {
            "1. Compose Multiplatform UI": [
                "org.jetbrains.compose.runtime:runtime",
                "org.jetbrains.compose.material3:material3",
                "org.jetbrains.androidx.navigation:navigation-compose",
            ],
            "2. Networking (Ktor)": [
                "io.ktor:ktor-client-core",
                "io.ktor:ktor-client-content-negotiation",
                "io.ktor:ktor-serialization-kotlinx-json",
                "io.ktor:ktor-client-okhttp",
                "io.ktor:ktor-client-darwin",
            ],
            "3. Dependency Injection (Koin)": ["io.insert-koin:koin-core", "io.insert-koin:koin-compose"],
            "4. Async & Serialization": [
                "org.jetbrains.kotlinx:kotlinx-coroutines-core",
                "org.jetbrains.kotlinx:kotlinx-serialization-json",
            ],
            "5. Images": ["io.coil-kt.coil3:coil-compose", "io.coil-kt.coil3:coil-network-ktor3"],
            "6. Shared Database & Wishlist": [
                "app.cash.sqldelight:runtime",
                "app.cash.sqldelight:coroutines-extensions",
                "com.russhwolf:multiplatform-settings",
            ],
            "7. Android-only": ["androidx.activity:activity-compose"],
            "8. Testing": ["org.jetbrains.kotlin:kotlin-test", "app.cash.turbine:turbine"],
        },
    },
    "chat": {
        "name": "💬 Realtime Chat & Messaging (Compose Multiplatform)",
        "description": "Shared websocket transport, message store and presence across platforms.",
        "modules": {
            "1. Compose Multiplatform UI": [
                "org.jetbrains.compose.runtime:runtime",
                "org.jetbrains.compose.material3:material3",
                "org.jetbrains.androidx.navigation:navigation-compose",
            ],
            "2. Realtime Transport (Ktor WebSockets)": [
                "io.ktor:ktor-client-core",
                "io.ktor:ktor-client-websockets",
                "io.ktor:ktor-client-okhttp",
                "io.ktor:ktor-client-darwin",
            ],
            "3. Dependency Injection (Koin)": ["io.insert-koin:koin-core", "io.insert-koin:koin-compose"],
            "4. Async & Serialization": [
                "org.jetbrains.kotlinx:kotlinx-coroutines-core",
                "org.jetbrains.kotlinx:kotlinx-serialization-json",
                "org.jetbrains.kotlinx:kotlinx-datetime",
            ],
            "5. Images & Attachments": ["io.coil-kt.coil3:coil-compose"],
            "6. Shared Message Cache": [
                "app.cash.sqldelight:runtime",
                "app.cash.sqldelight:coroutines-extensions",
            ],
            "7. Android-only": ["androidx.activity:activity-compose"],
            "8. Testing": ["org.jetbrains.kotlin:kotlin-test", "app.cash.turbine:turbine"],
        },
    },
    "standard": {
        "name": "🧱 Standard Compose Multiplatform Baseline",
        "description": "The unopinionated shared-module starting point: UI, Ktor, DI, storage, tests.",
        "modules": {
            "1. Compose Multiplatform UI": [
                "org.jetbrains.compose.runtime:runtime",
                "org.jetbrains.compose.material3:material3",
                "org.jetbrains.androidx.navigation:navigation-compose",
            ],
            "2. Networking (Ktor)": [
                "io.ktor:ktor-client-core",
                "io.ktor:ktor-client-content-negotiation",
                "io.ktor:ktor-serialization-kotlinx-json",
                "io.ktor:ktor-client-okhttp",
                "io.ktor:ktor-client-darwin",
            ],
            "3. Dependency Injection (Koin)": ["io.insert-koin:koin-core", "io.insert-koin:koin-compose"],
            "4. Async & Serialization": [
                "org.jetbrains.kotlinx:kotlinx-coroutines-core",
                "org.jetbrains.kotlinx:kotlinx-serialization-json",
            ],
            "5. Shared Storage": ["com.russhwolf:multiplatform-settings"],
            "6. Android-only": ["androidx.activity:activity-compose"],
            "7. Testing": ["org.jetbrains.kotlin:kotlin-test", "app.cash.turbine:turbine"],
        },
    },
}

# Which source set each coordinate belongs to. Anything unlisted is commonMain —
# getting this wrong is the classic KMP failure (a JVM-only artifact in commonMain
# fails to resolve for the iOS target, with a confusing error).
SOURCE_SETS = {
    "io.ktor:ktor-client-okhttp": ANDROID,
    "androidx.activity:activity-compose": ANDROID,
    "com.google.maps.android:maps-compose": ANDROID,
    "com.google.android.gms:play-services-location": ANDROID,
    "io.ktor:ktor-client-darwin": IOS,
}

TEST_COORDS = {"org.jetbrains.kotlin:kotlin-test", "app.cash.turbine:turbine"}

STABLE_DEFAULTS = {
    "org.jetbrains.compose.runtime:runtime": "1.7.3",
    "org.jetbrains.compose.material3:material3": "1.7.3",
    "org.jetbrains.androidx.navigation:navigation-compose": "2.8.0-alpha11",
    "io.ktor:ktor-client-core": "3.0.3",
    "io.ktor:ktor-client-content-negotiation": "3.0.3",
    "io.ktor:ktor-serialization-kotlinx-json": "3.0.3",
    "io.ktor:ktor-client-okhttp": "3.0.3",
    "io.ktor:ktor-client-darwin": "3.0.3",
    "io.ktor:ktor-client-websockets": "3.0.3",
    "io.insert-koin:koin-core": "4.0.1",
    "io.insert-koin:koin-compose": "4.0.1",
    "org.jetbrains.kotlinx:kotlinx-coroutines-core": "1.9.0",
    "org.jetbrains.kotlinx:kotlinx-serialization-json": "1.7.3",
    "org.jetbrains.kotlinx:kotlinx-datetime": "0.6.1",
    "io.coil-kt.coil3:coil-compose": "3.0.4",
    "io.coil-kt.coil3:coil-network-ktor3": "3.0.4",
    "app.cash.sqldelight:runtime": "2.0.2",
    "app.cash.sqldelight:coroutines-extensions": "2.0.2",
    "com.russhwolf:multiplatform-settings": "1.3.0",
    "androidx.activity:activity-compose": "1.10.0",
    "com.google.maps.android:maps-compose": "6.4.1",
    "com.google.android.gms:play-services-location": "21.3.0",
    "org.jetbrains.kotlin:kotlin-test": "2.1.0",
    "app.cash.turbine:turbine": "1.2.0",
}


# Build-plugin versions are not library coordinates, so they are pinned rather than resolved.
TOOLCHAIN = {"kotlin": "2.1.0", "agp": "8.7.3", "composeMultiplatform": "1.7.3"}


def resolve_google_maven(group, artifact):
    url = (f"https://dl.google.com/dl/android/maven2/{group.replace('.', '/')}"
           f"/{artifact}/maven-metadata.xml")
    status, body = http_get(url)
    if status != 200 or not body:
        return None
    try:
        root = ET.fromstring(body)
        return latest_stable([v.text for v in root.findall('.//version') if v.text])
    except ET.ParseError:
        return None


def resolve_maven_central(group, artifact):
    query = urllib.parse.quote(f'g:"{group}" AND a:"{artifact}"')
    data = get_json(f"https://search.maven.org/solrsearch/select?q={query}&rows=5&wt=json")
    if not data:
        return None
    docs = data.get('response', {}).get('docs', [])
    if docs:
        return docs[0].get('latestVersion') or docs[0].get('v')
    return None


def resolve_coord(coord):
    group, artifact = coord.split(':', 1)
    if group.startswith('androidx.') or group.startswith('com.google.') \
            or group.startswith('org.jetbrains.androidx.'):
        version = resolve_google_maven(group, artifact)
        if version:
            return version, "Google"
    version = resolve_maven_central(group, artifact)
    if version:
        return version, "Central"
    return None, None


def _alias(coord):
    group, artifact = coord.split(':', 1)
    key = artifact.replace('-', '.').replace('_', '.')
    prefix = {"io.ktor": "ktor", "io.insert-koin": "koin", "app.cash.sqldelight": "sqldelight",
              "io.coil-kt.coil3": "coil"}.get(group)
    return f"{prefix}.{key}" if prefix and not key.startswith(prefix) else key


def _version_ref(coord):
    """Artifacts released in lockstep share one version ref — that is the point of a catalog."""
    group = coord.split(':', 1)[0]
    shared = {"io.ktor": "ktor", "io.insert-koin": "koin", "app.cash.sqldelight": "sqldelight",
              "io.coil-kt.coil3": "coil", "org.jetbrains.compose.runtime": "composeMultiplatform",
              "org.jetbrains.compose.material3": "composeMultiplatform"}
    return shared.get(group) or _alias(coord).replace('.', '')


def generate_toml(app_data, resolved):
    versions, libraries = {}, []
    for packages in app_data["modules"].values():
        for coord in packages:
            ref = _version_ref(coord)
            versions.setdefault(ref, resolved[coord]['version'])
            group, artifact = coord.split(':', 1)
            libraries.append((_alias(coord), group, artifact, ref))

    # The [plugins] block below references these, so they must exist in [versions].
    versions.setdefault("kotlin", TOOLCHAIN["kotlin"])
    versions.setdefault("agp", TOOLCHAIN["agp"])
    versions.setdefault("composeMultiplatform", TOOLCHAIN["composeMultiplatform"])

    lines = [f"# {app_data['name']}", "", "[versions]"]
    lines += [f'{k} = "{v}"' for k, v in sorted(versions.items())]
    lines += ["", "[libraries]"]
    for alias, group, artifact, ref in sorted(set(libraries)):
        lines.append(f'{alias} = {{ module = "{group}:{artifact}", version.ref = "{ref}" }}')
    lines += ["", "[plugins]",
              'kotlinMultiplatform = { id = "org.jetbrains.kotlin.multiplatform", version.ref = "kotlin" }',
              'androidLibrary = { id = "com.android.library", version.ref = "agp" }',
              'composeMultiplatform = { id = "org.jetbrains.compose", version.ref = "composeMultiplatform" }',
              'kotlinSerialization = { id = "org.jetbrains.kotlin.plugin.serialization", version.ref = "kotlin" }']
    return "\n".join(lines)


def generate_dsl(app_data, resolved):
    buckets = {COMMON: [], ANDROID: [], IOS: [], "test": []}
    for packages in app_data["modules"].values():
        for coord in packages:
            if coord in TEST_COORDS:
                buckets["test"].append(coord)
            else:
                buckets[SOURCE_SETS.get(coord, COMMON)].append(coord)

    def deps(coords, indent="            "):
        return [f'{indent}implementation(libs.{_alias(c)})' for c in sorted(set(coords))]

    lines = [
        f"// {app_data['name']}",
        "plugins {",
        "    alias(libs.plugins.kotlinMultiplatform)",
        "    alias(libs.plugins.androidLibrary)",
        "    alias(libs.plugins.composeMultiplatform)",
        "    alias(libs.plugins.kotlinSerialization)",
        "}",
        "",
        "kotlin {",
        "    androidTarget()",
        "    listOf(iosX64(), iosArm64(), iosSimulatorArm64()).forEach { target ->",
        "        target.binaries.framework {",
        '            baseName = "Shared"',
        "            isStatic = true",
        "        }",
        "    }",
        "",
        "    sourceSets {",
        "        commonMain.dependencies {",
    ]
    lines += deps(buckets[COMMON])
    lines += ["        }", "", "        androidMain.dependencies {"]
    lines += deps(buckets[ANDROID])
    lines += ["        }", "", "        iosMain.dependencies {"]
    lines += deps(buckets[IOS])
    lines += ["        }", "", "        commonTest.dependencies {"]
    lines += [f'            implementation(libs.{_alias(c)})' for c in sorted(set(buckets["test"]))]
    lines += [
        "        }",
        "    }",
        "}",
        "",
        "android {",
        '    namespace = "com.example.shared"',
        "    compileSdk = 35",
        "    defaultConfig { minSdk = 24 }",
        "}",
    ]
    return "\n".join(lines)


def main():
    parser = build_parser(
        PROG, "🎼 Composer KMP Maestro — Compose Multiplatform stack architect", CATALOGS,
        [("toml", "Output libs.versions.toml"), ("dsl", "Output build.gradle.kts")],
    )
    args = parser.parse_args()
    app_data = CATALOGS[args.app]

    print_header("🎼 COMPOSER KMP MAESTRO (v1.0)", app_data)

    if args.offline:
        log(f"{C['GRAY']}📴 Offline mode — using curated stable versions.{C['RESET']}")
        resolver = Resolver(lambda c: (None, None), STABLE_DEFAULTS)
    else:
        log(f"{C['GRAY']}📡 Contacting Google Maven & Maven Central...{C['RESET']}")
        resolver = Resolver(resolve_coord, STABLE_DEFAULTS)
    resolved = resolver.resolve_all(app_data["modules"])

    if args.toml:
        write_out(generate_toml(app_data, resolved), args.out)
    elif args.dsl:
        write_out(generate_dsl(app_data, resolved), args.out)
    elif args.agent_manifest:
        write_out(generate_agent_manifest("kmp", args.app, app_data, resolved), args.out)
    else:
        log("")
        print_stack(app_data["modules"], resolved)
        print_quick_actions(PROG, args.app, [
            ("toml", "Generate libs.versions.toml"),
            ("dsl", "Generate build.gradle.kts"),
            ("agent-manifest", "Generate AI context"),
        ])


if __name__ == "__main__":
    main()
