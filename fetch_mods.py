#!/usr/bin/env python3
"""Fetch the mods listed in mods.txt into ./mods/.

Sources (one entry per line, #comments and blank lines ignored):

    modrinth:<slug>[@<version>]      newest (or pinned) Fabric build for MC_VERSION
    github:<owner>/<repo>[@<tag>]    .jar asset(s) from that GitHub release

Pinned:  modrinth:fabric-api@0.166.2+26.3
Latest:  modrinth:fabric-api

Every download is verified against the sha512 reported by Modrinth. Jars in ./mods
that are not in the resolved set are removed, so a machine that pulls a new mod set
does not keep stale versions around.
"""

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

MC_VERSION = os.environ.get("MC_VERSION", "26.3")
LOADER = os.environ.get("MOD_LOADER", "fabric")
USER_AGENT = "YOLTServer-fetch/1.0 (github.com/BobbyNooby/YOLTServer)"
MODS_DIR = "mods"
LIST_FILE = "mods.txt"


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} for {url}") from None
    except urllib.error.URLError as e:
        raise SystemExit(f"network error for {url}: {e.reason}") from None


def download(url, path, sha512=None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    h = hashlib.sha512()
    with urllib.request.urlopen(req, timeout=300) as r, open(path + ".part", "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
            h.update(chunk)
    if sha512 and h.hexdigest() != sha512:
        os.unlink(path + ".part")
        raise SystemExit(f"sha512 mismatch for {os.path.basename(path)}")
    os.replace(path + ".part", path)


def parse(entry):
    source, _, rest = entry.partition(":")
    if not rest:
        raise SystemExit(f"bad entry (expected 'source:id'): {entry}")
    name, _, pin = rest.partition("@")
    return source.strip(), name.strip(), pin.strip() or None


def modrinth(slug, pin):
    url = (
        f"https://api.modrinth.com/v2/project/{slug}/version"
        f"?loaders=%5B%22{LOADER}%22%5D&game_versions=%5B%22{MC_VERSION}%22%5D"
    )
    versions = get_json(url)
    if not versions:
        raise SystemExit(f"{slug}: no {LOADER} build for Minecraft {MC_VERSION}")
    if pin:
        versions = [v for v in versions if v["version_number"] == pin or v["id"] == pin]
        if not versions:
            raise SystemExit(f"{slug}: pinned version {pin} not found for {MC_VERSION}")
    v = versions[0]
    files = [f for f in v["files"] if f.get("primary")] or v["files"]
    f = files[0]
    return [(f["filename"], f["url"], f["hashes"].get("sha512"), f"{slug} {v['version_number']}")]


def github(repo, tag):
    base = f"https://api.github.com/repos/{repo}/releases"
    rel = get_json(f"{base}/tags/{tag}") if tag else get_json(f"{base}/latest")
    if rel.get("draft"):
        raise SystemExit(f"{repo}: release {rel.get('tag_name')} is a draft — publish it first")
    jars = [a for a in rel.get("assets", []) if a["name"].endswith(".jar")]
    if not jars:
        raise SystemExit(f"{repo}: no .jar asset on release {rel.get('tag_name')}")
    return [(a["name"], a["browser_download_url"], None, f"{repo} {rel['tag_name']}") for a in jars]


def main():
    if not os.path.exists(LIST_FILE):
        raise SystemExit(f"{LIST_FILE} not found")
    os.makedirs(MODS_DIR, exist_ok=True)

    entries = []
    with open(LIST_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                entries.append(line)

    wanted, failed = set(), []
    for entry in entries:
        source, name, pin = parse(entry)
        try:
            if source == "modrinth":
                results = modrinth(name, pin)
            elif source == "github":
                results = github(name, pin)
            else:
                raise SystemExit(f"unknown source '{source}' in: {entry}")
            for filename, url, sha, label in results:
                path = os.path.join(MODS_DIR, filename)
                if os.path.exists(path):
                    print(f"  ok    {filename}  ({label})")
                else:
                    print(f"  get   {filename}  ({label})")
                    download(url, path, sha)
                wanted.add(filename)
        except SystemExit as e:
            failed.append(f"{entry}: {e}")

    for stale in sorted(f for f in os.listdir(MODS_DIR) if f.endswith(".jar") and f not in wanted):
        os.unlink(os.path.join(MODS_DIR, stale))
        print(f"  rm    {stale}  (not in mods.txt)")

    print(f"\n{len(wanted)} mod(s) in {MODS_DIR}/ for Minecraft {MC_VERSION} / {LOADER}")
    if failed:
        print("\nfailures:")
        for f in failed:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
