# Security course

A self-paced cybersecurity course, published as a static site with GitHub Pages. You work through it one unit a week, in short daily sessions built around real incidents, with a lab every week. A Claude Code routine acts as the tutor: once a week it publishes the next unit, gives feedback on your lab notes, and writes a short news page that ties current events back to what you've learned.

## How a week works

| Day | Session | Time |
|---|---|---|
| Monday | The incident: what happened and why it worked | 20 min |
| Tuesday | How the attack works | 20 min |
| Wednesday | Prevention and detection | 20 min |
| Thursday | Lab prep: setup and briefing | 30 min |
| Friday | Off | |
| Saturday | The lab | about 2 h |
| Sunday | Review quiz, then log your progress | 15 min |

On Sunday evening the routine runs. If you've logged the lab in `me/progress.yaml`, it writes a debrief of your notes and publishes the next unit for the coming week. If you haven't, it waits, so the course never gets ahead of you. Either way it writes that week's news page.

The site rebuilds every morning, so the home page always opens on today's session.

## What's where

```
course/                yours; the routine reads these and never edits them
  units.yaml           the syllabus: 36 units, in order
  cases.yaml           real incidents the lessons are built on, with sources
  labs.yaml            one lab per unit
  link-hosts.txt       the only hosts the routine's pages may link to
me/                    yours
  progress.yaml        log each unit's lab here when you finish it
  notes/<unit>.md      your lab notes; the routine reads them for the debrief
units/<unit>/          the routine's: day-1.md to day-6.md, then debrief.md
news/YYYY-Www.md       the routine's: one news page a week
digest/                the routine's instructions, feeds, and your requests
build.py, theme/       turn all of this into the site, after checking it
tests/                 tests for build.py
.github/workflows/     tests, deploy (on push and every morning), and publishing the routine's branch
ROUTINE_PROMPT.md      the text to paste into the routine
```

## Using it

- **Finish a lab:** add an entry to `me/progress.yaml` with the date and how confident you feel, from 1 to 5. Each unit page shows the exact lines to paste. A confidence of 1 or 2 brings that unit back into later reviews.
- **Take notes:** write them in `me/notes/<unit slug>.md`. The next debrief responds to them. The lab-prep day gives you a template.
- **Check sources before they're used:** the routine only uses incidents and labs whose `checked` field holds a date. Open the sources, read the entry, and set `checked:` to the date you checked it, year first, as in `checked: 2026-11-02`. Values like `yes` or `true` fail the build. Check a few weeks ahead of where you are.
- **Ask for something:** add a line under "Open" in `digest/requests.md`. The next run works it into the week or the debrief.
- **Change the course:** reorder, edit or cut units in `course/units.yaml`. Keep each unit's slug once it's been taught.

If this repository is public, so are your progress file and notes.

## Setup

### 1. Repository and Pages

In the repository, go to **Settings → Pages → Build and deployment** and set **Source** to **GitHub Actions**. A public repository works on a free account; GitHub Pages for a private repository needs GitHub Pro, which is free through the GitHub Student Developer Pack. The published site is public either way.

Every push to main runs **Deploy site**, which publishes to `https://<your-username>.github.io/<repository>/`. If a deploy fails, open the run in the Actions tab and expand the **Build** step: it lists every problem it found.

### 2. A network policy for the routine

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

When the routine hits a site that isn't allowed, it lists the hostname under "Blocked hosts" in `digest/sources.md` so you can decide whether to add it. Keep this list and `course/link-hosts.txt` in step: the routine should only link to pages it could actually read.

### 3. Create the routine

At [claude.ai/code/routines](https://claude.ai/code/routines), click **New routine**:

- **Name:** Security course
- **Prompt:** paste the contents of `ROUTINE_PROMPT.md`, and pick a model
- **Repository:** this repository only
- **Environment:** the one from step 2
- **Trigger:** Schedule, Weekly, Sunday evening (for example 20:00)
- **Connectors:** remove all of them. The routine reads untrusted web pages and acts without asking, so it should hold nothing beyond this repository.

### 4. First run

1. Check the first unit's lab in `course/labs.yaml`, and ideally its incidents in `course/cases.yaml`, by setting their `checked` dates. The routine won't publish a unit whose lab isn't checked.
2. On the routine's page, click **Run now**. Run it on a Saturday or Sunday, and the unit's week starts the coming Monday.
3. Open the run and read what it did: a green status only means the session didn't crash. Then check the Actions tab and the site.

The routine pushes to a `claude/brief-<date>` branch, never to main. The **Check** workflow runs the tests and the build on that branch, and when they pass, **Publish the routine's branch** checks that only `units/`, `news/` and `digest/` changed, fast-forwards main and deploys. That last check always runs from the copy on main, so the routine can't change it. Name your own branches something else, or they'll be published the same way.

### 5. Optional: notifications

Subscribe to `https://<your-username>.github.io/<repository>/feed.xml` in a feed reader. Each day's session appears in it on its morning.

## What the build checks

Pages written by the routine are checked before anything is published. The build fails, listing every problem, if:

- a unit's day files are missing, out of order, or have bad front matter
- a lab or incident is used before you've checked it
- a unit is published before you've logged the previous unit's lab
- a page links to a host that isn't allowed

The Markdown is then sanitized, so no scripts, event handlers or images reach a page, and the site's Content Security Policy blocks scripts entirely. Your own files are checked too: `me/progress.yaml` and the cross-references in `course/`.

## Working on it locally

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest
python build.py && python -m http.server -d _site
```
