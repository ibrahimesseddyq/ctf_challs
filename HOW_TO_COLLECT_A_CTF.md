# How to collect a CTF

How to archive a finished CTF into `ctfdrive/`, in the same layout as `hacklu2026/`.

## 1. The target layout

```
ctfdrive/<ctfname><year>/
├── info                    # one line: format:FLAGPREFIX{...}
├── crypto/                 # one folder per category (short lowercase names)
│   ├── Challenge_Name      # text file, no extension (see below)
│   └── challenge.zip       # the handout file(s), as downloaded
├── rev/  pwn/  web/  misc/  forensics/  steg/  osint/  hardware/  blockchain/ ...
```

Each challenge text file holds four fields:

```
a:<author>
p:<points at the end of the CTF>
s:<number of solves>
d:<the challenge description, as shown to players>
```

Category names: `crypto`, `rev`, `pwn`, `web`, `misc`, `forensics`, `steg`, `osint`, `hardware`,
`blockchain`, `network`, `android`/`mobile`, `ai`. Map the platform's names onto these (e.g.
"Reverse Engineering" → `rev`, "Cryptography" → `crypto`, "AI / LLM" → `ai`).

## 2. Quick path: the script

```
cd ~/Desktop/ctfdrive
python3 collect_ctf.py <ctftime-event-id> <folder>          # e.g. 3460 hicybercon2026
python3 collect_ctf.py 3460 hicybercon2026 --no-files       # info files only, no downloads
python3 collect_ctf.py 3460 hicybercon2026 --token XXXX     # if the platform needs a login
```

It handles **rCTF** and **CTFd** platforms. It prints the flag-format guess and every file that failed or
whose SHA-256 didn't match. Always do the checks in step 4 afterwards.

If it says the platform isn't supported, or nothing is public, collect by hand (step 3).

## 3. By hand, step by step

### 3.1 Find the event on CTFtime

`https://ctftime.org/api/v1/events/<id>/` gives the title, dates, organizer, weight and the platform
`url`. Example: event 3460 = HI Cyber Con 2026 CTF, `https://ctf.hiddeninvestigations.net/`.

### 3.2 Identify the platform

```
curl -s https://<platform>/api/v1/challs        # rCTF: {"kind":"goodChallenges", ...}
curl -s https://<platform>/api/v1/challenges    # CTFd: {"success":true, ...}
```

* **rCTF** (SvelteKit/React front end, errors look like `{"kind":"badEndpoint"}`):
  `/api/v1/challs` lists everything in one call: name, category, author, points, solves, description, files.
  It's often public once the CTF has ended. The flag format and settings are in `/api/v1/integrations/client/config`.
* **CTFd** (`/themes/core/...`, cookie `session`): `/api/v1/challenges` is the list.
  `/api/v1/challenges/<id>` holds the description, files and author. Solves are in the list or `/api/v1/challenges/<id>/solves`.
  It usually needs a login: create an account, go to Settings → Access Tokens, and use `Authorization: Token <token>`.
* **Anything else** (custom platforms, closed scoreboards): look at the page's network requests in
  the browser dev tools, or use the organizers' GitHub repo. Many teams publish `<ctf>-<year>-challenges`
  after the event, which often has the handouts and sometimes the original descriptions.

### 3.3 Write the challenge files

For each challenge, write `<category>/<Challenge_Name>` with `a:/p:/s:/d:`. Replace spaces and odd characters
in the name with `_`. Keep the description as shown, but remove the platform-added lines
(`**Files:** ...`, `SHA-256: ...`, `**Flag Format:** ...`), since the files sit next to it and the format goes in `info`.

### 3.4 Download the handouts

Files are either in the API's `files` list, or (on rCTF setups like HI Cyber Con) linked inside the
description as `[name.zip](https://...objectstorage...)` together with a `SHA-256:` line.

* Save them in the category folder under their original name. If two challenges share a filename,
  prefix it with the challenge name.
* Check the SHA-256 whenever the description gives one.
* **Check sizes first** (`curl -sI <url> | grep -i content-length`). Forensics dumps can be huge:
  HI Cyber Con 2026 was 3.8 GB in total, with a 1.7 GB RAM image.
* Don't unzip or run anything you download. Archive it as is.
* Download soon after the CTF ends. Bucket links and instances often go offline within days or weeks.

### 3.5 Write `info`

`format:<PREFIX>{...}`. Look for it in the rules page, the CTFtime description or the challenge descriptions.
The most common `PREFIX{` across descriptions is usually right, but confirm it.

## 4. Checks before you're done

- [ ] The number of challenge files equals the platform's challenge count.
- [ ] Every challenge that had a handout has its file, and there are no `FAIL` or `SHA-MISMATCH` lines.
- [ ] `info` holds the right flag format.
- [ ] Points and solves are the **final** values (collect after the CTF ends, not during it).
- [ ] Authors are spelled consistently (HI Cyber Con had "Hidden Investigtaions" once).
- [ ] The raw API dump is kept (`.challs.raw.json`), in case a field needs re-reading later.

## 5. Things that don't come with the collection

- **Instance-only challenges** (web/pwn with "request an instance" and no handout): only the
  description survives. Note it in the description if no source is available.
- **Dynamic scoring**: points drop as solves rise. Record the final value.
- **Hidden or removed challenges** don't appear in the API. Compare with the CTFtime task list.
- **Writeups**: link them later on ctf42; the CTFtime event page lists them under "Tasks".

## Example: HI Cyber Con 2026 CTF (CTFtime event 3460)

- Platform: rCTF at `ctf.hiddeninvestigations.net`. The challenge list was public after the event.
- 69 challenges in 13 categories, 61 handout files (3.8 GB) on a Hetzner object-storage bucket, each with a SHA-256 in its description.
- Flag format `hiCTF{...}`.
- Collected into `ctfdrive/hicybercon2026/` with `collect_ctf.py 3460 hicybercon2026`.
