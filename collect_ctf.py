#!/usr/bin/env python3
"""Collect a finished CTF into the ctfdrive layout.

    python3 collect_ctf.py <ctftime-event-id> <folder-name> [--token TOKEN] [--no-files]

Layout produced (same as hacklu2026/):
    <folder>/info                      flag format, e.g. "format:hiCTF{...}"
    <folder>/<category>/<Challenge>    text file: a:author  p:points  s:solves  d:description
    <folder>/<category>/<handout>      downloaded files (zip/tar/...), SHA-256 checked when given
    <folder>/.event.json               CTFtime event metadata
    <folder>/.challs.raw.json          raw challenge list from the platform API

Supported platforms: rCTF (/api/v1/challs) and CTFd (/api/v1/challenges). Anything else:
collect by hand (see HOW_TO_COLLECT_A_CTF.md).
"""
import argparse, collections, hashlib, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0"
CAT = {"reverse": "rev", "reversing": "rev", "reverse engineering": "rev", "re": "rev",
       "cryptography": "crypto", "crypto": "crypto", "steganography": "steg", "steg": "steg", "stego": "steg",
       "web": "web", "forensics": "forensics", "misc": "misc", "miscellaneous": "misc", "pwn": "pwn",
       "binary exploitation": "pwn", "hardware": "hardware", "blockchain": "blockchain", "osint": "osint",
       "network": "network", "networking": "network", "android": "android", "mobile": "mobile",
       "ai / llm": "ai", "ai": "ai", "llm": "ai"}


def get(url, token=None, auth=None):
    cmd = ["/usr/bin/curl", "-sL", "-A", UA, "--max-time", "60", url]
    if token:
        cmd[1:1] = ["-H", f"Authorization: {auth} {token}"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except ValueError:
        return None


def safe(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip()).strip("_") or "unnamed"


def rctf(base, token):
    d = get(base + "/api/v1/challs", token, "Bearer")
    if not d or d.get("kind") != "goodChallenges":
        return None
    out = []
    for c in d["data"]:
        files = [(f["name"], f["url"]) for f in c.get("files") or []]
        out.append(dict(name=c["name"], category=c["category"], author=c.get("author", ""),
                        points=c.get("points"), solves=c.get("solves"), description=c.get("description", ""),
                        files=files))
    return d["data"], out


def ctfd(base, token):
    lst = get(base + "/api/v1/challenges", token, "Token")
    if not lst or not lst.get("success"):
        return None
    raw, out = [], []
    for c in lst["data"]:
        full = (get(f"{base}/api/v1/challenges/{c['id']}", token, "Token") or {}).get("data", c)
        raw.append(full)
        files = [(f.split("/")[-1].split("?")[0], base + f if f.startswith("/") else f) for f in full.get("files") or []]
        out.append(dict(name=full["name"], category=full.get("category", "misc"), author=full.get("author", ""),
                        points=full.get("value"), solves=full.get("solves"), description=full.get("description", ""),
                        files=files))
    return raw, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("event_id")
    ap.add_argument("folder")
    ap.add_argument("--token", help="platform API token, only if the challenge list needs a login")
    ap.add_argument("--no-files", action="store_true", help="write info files only, skip downloads")
    a = ap.parse_args()

    ev = get(f"https://ctftime.org/api/v1/events/{a.event_id}/")
    if not ev:
        sys.exit("CTFtime event not found")
    base = ev["url"].rstrip("/")
    print(f"{ev['title']} | {ev['start'][:10]} -> {ev['finish'][:10]} | platform {base}")

    got = rctf(base, a.token) or ctfd(base, a.token)
    if not got:
        sys.exit("Platform is not rCTF/CTFd, or the challenge list needs a login (pass --token). Collect by hand.")
    raw, challs = got

    root = os.path.abspath(a.folder)
    os.makedirs(root, exist_ok=True)
    json.dump(ev, open(f"{root}/.event.json", "w"), indent=1)
    json.dump(raw, open(f"{root}/.challs.raw.json", "w"), indent=1, ensure_ascii=False)

    # Flag format: most common PREFIX{ seen in descriptions (check it by hand afterwards).
    prefixes = collections.Counter(m for c in challs for m in re.findall(r"\b([A-Za-z0-9_]{2,20})\{", c["description"]))
    fmt = prefixes.most_common(1)[0][0] + "{...}" if prefixes else "UNKNOWN - fill in by hand"
    open(f"{root}/info", "w").write(f"format:{fmt}\n")

    downloads, used = [], set()
    for c in challs:
        cat = CAT.get(c["category"].strip().lower(), safe(c["category"].lower()))
        os.makedirs(f"{root}/{cat}", exist_ok=True)
        name = safe(c["name"])
        desc = c["description"]
        # Handouts linked inside the description (common on rCTF): [file.zip](https://...)
        linked = re.findall(r"\[([^\]]+)\]\((https?://[^)]+\.(?:zip|tar|gz|tgz|7z|xz|rar|bin|elf|exe|apk|pcap|pcapng|png|jpg|wav|txt|py|raw|img|E01|vmem))\)", desc, re.I)
        shas = re.findall(r"SHA-?256:?\s*`?([0-9a-f]{64})", desc, re.I)
        desc = re.sub(r"\*\*Files?:\*\*.*?(\n|$)|SHA-?256:.*?(\n|$)|\*\*Flag Format:\*\*.*?(\n|$)", "", desc, flags=re.I).strip()
        open(f"{root}/{cat}/{name}", "w").write(f"a:{c['author']}\np:{c['points']}\ns:{c['solves']}\nd:{desc}\n")
        for i, (fn, url) in enumerate(c["files"] + linked):
            out = f"{cat}/{safe(fn)}"
            if out in used:
                out = f"{cat}/{name}_{safe(fn)}"
            used.add(out)
            downloads.append(dict(url=url, out=out, sha=shas[i] if i < len(shas) else ""))
    json.dump(downloads, open(f"{root}/.downloads.json", "w"), indent=0)
    print(f"{len(challs)} challenges, {len(downloads)} files, flag format guess: {fmt}")
    if a.no_files:
        return

    def fetch(x):
        p = f"{root}/{x['out']}"
        cmd = ["/usr/bin/curl", "-sfL", "--retry", "3", "-A", UA, "-o", p, x["url"]]
        if a.token and x["url"].startswith(base):
            cmd[1:1] = ["-H", f"Authorization: Token {a.token}"]
        if subprocess.run(cmd).returncode:
            return "FAIL " + x["out"]
        if not x["sha"]:
            return "ok-nosha " + x["out"]
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return ("ok " if h.hexdigest() == x["sha"] else "SHA-MISMATCH ") + x["out"]

    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(fetch, downloads))
    for r in res:
        if not r.startswith("ok "):
            print(r)
    print(f"downloaded {sum(not r.startswith('FAIL') for r in res)}/{len(res)}")


if __name__ == "__main__":
    main()
