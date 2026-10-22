# Daily security brief

A static site that a Claude Code routine updates every morning with one issue: top security stories, market moves, newly exploited vulnerabilities, one concept from a learning track (attack, prevention, detection), and one hands-on lab.

```
posts/                 one Markdown file per issue (written by the routine)
digest/INSTRUCTIONS.md what the routine does on each run
digest/curriculum.md   the learning track, ticked off as it goes
digest/requests.md     topics you want covered next
digest/sources.md      feeds the routine reads
build.py, theme/       turns posts into the site (sanitized HTML, Atom feed)
.github/workflows/     deploy to GitHub Pages; fast-forward main from claude/ branches
ROUTINE_PROMPT.md      the text to paste into the routine
```

## Setup

### 1. Create the repository

Create an empty repository on GitHub, for example `security-brief`. A public repository works on a free account; GitHub Pages for a private repository needs GitHub Pro, which is free through the GitHub Student Developer Pack. The published site is public either way.

In the repository, go to **Settings → Pages → Build and deployment** and set **Source** to **GitHub Actions**.

### 2. Push this folder

```sh
cd security-brief
git init -b main
git add .
git commit -m "Set up the brief"
git remote add origin git@github.com:<your-username>/security-brief.git
git push -u origin main
```

The **Deploy site** workflow runs and publishes the welcome issue at `https://<your-username>.github.io/security-brief/`. Make the first commit yourself: the routine can push straight to main only while every commit on main is authored by you.

### 3. Give the routine a network policy

Cloud sessions use the **Trusted** network policy by default, which blocks news sites. Create a separate environment for this routine (environment picker at claude.ai/code, or from the routine form) and set **Network access** to **Custom** with **Also include default list of common package managers** checked, then paste these allowed domains:

```
therecord.media
www.bleepingcomputer.com
bleepingcomputer.com
krebsonsecurity.com
www.securityweek.com
securityweek.com
www.darkreading.com
darkreading.com
arstechnica.com
feeds.feedburner.com
thehackernews.com
www.cisa.gov
cisa.gov
nvd.nist.gov
services.nvd.nist.gov
isc.sans.edu
googleprojectzero.blogspot.com
portswigger.net
blog.talosintelligence.com
unit42.paloaltonetworks.com
www.microsoft.com
securelist.com
www.schneier.com
www.returnonsecurity.com
strategyofsecurity.com
news.crunchbase.com
risky.biz
tldrsec.com
www.enisa.europa.eu
attack.mitre.org
owasp.org
cheatsheetseries.owasp.org
tryhackme.com
www.hackthebox.com
academy.hackthebox.com
overthewire.org
picoctf.org
cyberdefenders.org
blueteamlabs.online
```

When the routine hits a site that isn't allowed, it lists the hostname under "Blocked hosts" in `digest/sources.md` so you can decide whether to add it. **Full** network access also works and needs no list, at the cost of letting the routine reach anything.

### 4. Create the routine

At [claude.ai/code/routines](https://claude.ai/code/routines), click **New routine**:

- **Name:** Daily security brief
- **Prompt:** paste the contents of `ROUTINE_PROMPT.md`, and pick a model
- **Repository:** this repository only
- **Environment:** the one from step 3
- **Trigger:** Schedule, Daily, at the time you want it ready
- **Connectors:** remove all of them. The routine reads untrusted web pages and acts without asking, so it should hold nothing beyond this repository.

Click **Create**, then **Run now** on the routine's page. A green run status only means the session didn't crash, so open the run and read what it did. Then check the Actions tab and the site.

### 5. Optional: notifications

Subscribe to `https://<your-username>.github.io/security-brief/feed.xml` in any feed reader app to get a notification when each issue lands.

## Steering

- Add a topic under "Open" in `digest/requests.md` to have the next issue cover it.
- Reorder or edit `digest/curriculum.md`; keep the `- [ ] ` lines and `## ` headings.
- Change length, tone, or sections in `digest/INSTRUCTIONS.md`.

Anything pushed to a `claude/` branch in this repository is fast-forwarded into main and published, including work from your own Claude Code sessions here.

## Preview locally

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python build.py && python -m http.server -d _site
```
