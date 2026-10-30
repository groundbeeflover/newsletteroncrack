#!/usr/bin/env python3
"""Build the course site into _site/.

Reads the syllabus in course/ and your progress in me/ (both yours), plus the
lessons in units/ and the weekly news in news/ (both written by the routine).

Everything the routine writes is checked before it reaches a page: required
files and front matter, references to units, cases and labs you have checked,
and the hosts its links point to. Its Markdown is then sanitized. A failed
check stops the build and lists every problem, so the routine can fix them all
and run the build again.

Run locally with:  python build.py && python -m http.server -d _site
"""

import datetime as dt
import html
import os
import re
import shutil
import sys
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

import markdown
import nh3
import yaml
from markdown.extensions.toc import slugify as toc_slugify

ROOT = Path(__file__).resolve().parent

SITE_TITLE = os.environ.get("SITE_TITLE", "Security course")
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")  # set by the deploy workflow

# Markdown in units/ and news/ is written by an agent that reads untrusted web
# content, so the rendered HTML is sanitized: no scripts, no event handlers, no
# inline styles, no images, no javascript: URLs. Only what a written lesson needs
# survives.
ALLOWED_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "code", "dd", "del", "details", "div",
    "dl", "dt", "em", "h2", "h3", "h4", "h5", "hr", "i", "kbd", "li", "ol", "p",
    "pre", "s", "strong", "sub", "summary", "sup", "table", "tbody", "td", "th",
    "thead", "tr", "ul",
}
ALLOWED_ATTRS = {
    "*": {"id"},
    "a": {"href", "title"},
    "abbr": {"title"},
    "code": {"class"},
    "td": {"align"},
    "th": {"align"},
    "ol": {"start"},
}

# Files a unit folder may hold, in page order. The routine publishes a unit with
# the first three; the review and the debrief of your lab notes come later.
UNIT_PARTS = {
    "lesson-1.md": "Lesson 1",
    "lesson-2.md": "Lesson 2",
    "lab.md": "Lab guide",
    "review.md": "Review",
    "debrief.md": "Debrief",
}
REQUIRED_PARTS = ("lesson-1.md", "lesson-2.md", "lab.md")

NEWS_NAME = re.compile(r"\d{4}-W\d{2}")
ATTACK_ID = re.compile(r"T\d{4}(\.\d{3})?")
FRONT_MATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
HREF = re.compile(r'href="([^"]*)"')

LAB_KINDS = {
    "platform": "hosted practice platform",
    "own-lab": "your own isolated lab",
    "writing": "writing exercise",
}

# Hosts where anyone can publish under the same name. A link there must match a
# URL listed in course/, not just the host, or one allowed repository would let
# the routine link to any repository.
SHARED_HOSTS = {
    "github.com", "githubusercontent.com", "gitlab.com", "bitbucket.org",
    "codeberg.org", "sourceforge.net", "docs.google.com", "drive.google.com",
    "sites.google.com", "dropbox.com", "onedrive.live.com", "1drv.ms", "mega.nz",
    "pastebin.com", "medium.com", "npmjs.com", "pypi.org", "hub.docker.com",
    "huggingface.co",
}

STATE_TEXT = {
    "done": "Done",
    "low": "Done, worth revisiting",
    "current": "In progress",
    "published": "Published",
    "todo": "Not started",
}


class BuildError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def nice_date(day: dt.date) -> str:
    return f"{day.day} {day.strftime('%B %Y')}"


def as_date(value):
    """A date from YAML (already a date) or an ISO string, else None."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def is_shared(host: str) -> bool:
    return any(host == shared or host.endswith("." + shared) for shared in SHARED_HOSTS)


def external(url: str) -> bool:
    parts = urlsplit(url)
    return bool(parts.scheme or parts.netloc)


class LinkAllowlist:
    """The external links that routine-written pages may contain."""

    def __init__(self):
        self.hosts: set[str] = set()
        self.prefixes: set[str] = set()

    def add(self, entry: str) -> bool:
        """Allow a host, or a URL prefix on a shared host. False if too broad."""
        if "://" in entry:
            parts = urlsplit(entry)
            host = (parts.hostname or "").lower()
            if is_shared(host):
                path = parts.path.rstrip("/")
                if not path:
                    return False
                self.prefixes.add(host + path)
                return True
        else:
            host = entry.lower().rstrip("/")
            if is_shared(host):
                return False
        if not host:
            return False
        self.hosts.add(host.removeprefix("www."))
        return True

    def permits(self, url: str) -> bool:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if parts.scheme not in ("http", "https", "") or not host:
            return False
        if is_shared(host):
            target = host + parts.path.rstrip("/")
            return any(target == p or target.startswith(p + "/") for p in self.prefixes)
        return any(host == h or host.endswith("." + h) for h in self.hosts)


def render_markdown(text: str, *, id_prefix: str = "", base_level: int = 1) -> str:
    rendered = markdown.markdown(
        text,
        extensions=["extra", "sane_lists", "toc"],
        extension_configs={"toc": {
            "permalink": False,
            # Shift headings down when the text sits under a section heading,
            # and prefix ids so two lessons on one page can't share an id.
            "baselevel": base_level,
            "slugify": lambda value, separator: id_prefix + toc_slugify(value, separator),
        }},
        output_format="html",
    )
    clean = nh3.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        url_schemes={"http", "https"},
        link_rel="noopener noreferrer",
    )
    # Let wide tables scroll inside their own box on small screens.
    clean = clean.replace("<table>", '<div class="table-wrap"><table>')
    return clean.replace("</table>", "</table></div>")


class Site:
    """Everything the pages are built from, loaded and checked."""

    def __init__(self, root: Path):
        self.root = root
        self.problems: list[str] = []
        self.load_course()
        if self.problems:  # everything after this relies on a consistent course
            raise BuildError(self.problems)
        self.allow = self.load_allowlist()
        self.progress = self.load_progress()
        self.content = self.load_unit_content()
        self.news = self.load_news()
        if self.problems:
            raise BuildError(self.problems)
        self.states = unit_states(self.units, self.content, self.progress)

    # Reporting

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def problem(self, path: Path, message: str) -> None:
        self.problems.append(f"{self.rel(path)}: {message}")

    def read_list(self, path: Path, key: str, required: bool = True) -> list[dict]:
        if not path.exists():
            if required:
                raise BuildError([f"{self.rel(path)}: file is missing"])
            return []
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise BuildError([f"{self.rel(path)}: not valid YAML ({exc})"]) from exc
        items = data.get(key) if isinstance(data, dict) else None
        if items is None and not required:
            return []
        if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
            raise BuildError([f"{self.rel(path)}: needs a top-level '{key}:' list of entries"])
        return items

    # Your files: course/ and me/

    def load_course(self) -> None:
        course = self.root / "course"
        cases_path, labs_path, units_path = (course / name for name in ("cases.yaml", "labs.yaml", "units.yaml"))

        self.cases = self.index(cases_path, "cases", ("id", "title", "year", "summary", "sources"))
        for case in self.cases.values():
            if not isinstance(case["year"], int):
                self.problem(cases_path, f"case '{case['id']}': year must be a number")
            if not all(isinstance(source, dict) for source in self.as_list(cases_path, case, "sources")):
                self.problem(cases_path, f"case '{case['id']}': each source needs kind, title and url")
                continue
            for source in case["sources"]:
                self.check_course_url(cases_path, f"case '{case['id']}'", source.get("url"))

        self.labs = self.index(labs_path, "labs", ("id", "name", "kind", "url"))
        for lab in self.labs.values():
            if lab["kind"] not in LAB_KINDS:
                self.problem(labs_path, f"lab '{lab['id']}': kind must be one of {', '.join(LAB_KINDS)}")
            extras = self.as_list(labs_path, lab, "extra")
            if not all(isinstance(extra, dict) for extra in extras):
                self.problem(labs_path, f"lab '{lab['id']}': each extra needs a title and url")
                continue
            for url in [lab["url"]] + [extra.get("url") for extra in extras]:
                self.check_course_url(labs_path, f"lab '{lab['id']}'", url)

        self.units, self.unit_by_slug = [], {}
        for number, unit in enumerate(self.read_list(units_path, "units"), 1):
            label = f"unit {number} ({unit.get('slug') or 'no slug'})"
            missing = [f for f in ("slug", "module", "title", "objectives", "lab") if not unit.get(f)]
            if missing:
                self.problem(units_path, f"{label} needs {', '.join(missing)}")
                continue
            if unit["slug"] in self.unit_by_slug:
                self.problem(units_path, f"{label}: slug is used twice")
                continue
            for field in ("objectives", "covers", "builds_on", "cases", "attack"):
                self.as_list(units_path, unit, field, label)
            for case in unit.get("cases") or []:
                if case not in self.cases:
                    self.problem(units_path, f"{label}: case '{case}' is not in course/cases.yaml")
            if unit["lab"] not in self.labs:
                self.problem(units_path, f"{label}: lab '{unit['lab']}' is not in course/labs.yaml")
            for earlier in unit.get("builds_on") or []:
                if earlier not in self.unit_by_slug:
                    self.problem(units_path, f"{label}: builds_on '{earlier}' is not an earlier unit")
            for technique in unit.get("attack") or []:
                if not ATTACK_ID.fullmatch(str(technique)):
                    self.problem(units_path, f"{label}: '{technique}' is not an ATT&CK technique ID")
            unit["number"] = number
            self.units.append(unit)
            self.unit_by_slug[unit["slug"]] = unit

    def index(self, path: Path, key: str, required: tuple[str, ...]) -> dict[str, dict]:
        entries = {}
        for item in self.read_list(path, key):
            ident = item.get("id") or "?"
            missing = [f for f in required if not item.get(f)]
            if missing:
                self.problem(path, f"entry '{ident}' needs {', '.join(missing)}")
                continue
            if ident in entries:
                self.problem(path, f"id '{ident}' is used twice")
                continue
            if item.get("checked") is not None and as_date(item["checked"]) is None:
                self.problem(path, f"entry '{ident}': checked must be a date (YYYY-MM-DD) or null")
            entries[ident] = item
        return entries

    def as_list(self, path: Path, entry: dict, field: str, label: str = "") -> list:
        value = entry.get(field) or []
        if not isinstance(value, list):
            self.problem(path, f"{label or entry.get('id')}: {field} must be a list")
            entry[field] = []
            return []
        return value

    def check_course_url(self, path: Path, label: str, url) -> None:
        if not isinstance(url, str) or urlsplit(url).scheme not in ("http", "https"):
            self.problem(path, f"{label}: {url!r} is not an http(s) URL")

    def load_allowlist(self) -> LinkAllowlist:
        allow = LinkAllowlist()
        path = self.root / "course" / "link-hosts.txt"
        if path.exists():
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                entry = line.split("#", 1)[0].strip()
                if entry and not allow.add(entry):
                    self.problem(path, f"line {number}: '{entry}' would allow too much; "
                                       "list a full repository or page URL for shared hosts")
        # Anything you've listed as a source or lab is fair to link to.
        for case in self.cases.values():
            for source in case["sources"]:
                allow.add(source["url"])
        for lab in self.labs.values():
            allow.add(lab["url"])
            for extra in lab.get("extra") or []:
                allow.add(extra["url"])
        return allow

    def load_progress(self) -> dict[str, dict]:
        path = self.root / "me" / "progress.yaml"
        progress = {}
        for entry in self.read_list(path, "progress", required=False):
            slug = entry.get("unit")
            if slug not in self.unit_by_slug:
                self.problem(path, f"unit '{slug}' is not in course/units.yaml")
                continue
            if slug in progress:
                self.problem(path, f"unit '{slug}' is listed twice")
                continue
            lab_done = entry.get("lab_done")
            if lab_done is not None and as_date(lab_done) is None:
                self.problem(path, f"{slug}: lab_done must be a date (YYYY-MM-DD) or left empty")
            confidence = entry.get("confidence")
            if confidence is not None and (isinstance(confidence, bool) or confidence not in range(1, 6)):
                self.problem(path, f"{slug}: confidence must be a whole number from 1 to 5")
            progress[slug] = {
                "lab_done": as_date(lab_done),
                "confidence": confidence,
                "note": str(entry.get("note") or ""),
            }
        return progress

    # The routine's files: units/ and news/

    def read_markdown(self, path: Path):
        text = path.read_text(encoding="utf-8")
        match = FRONT_MATTER.match(text)
        if not match:
            self.problem(path, "must start with front matter between two --- lines")
            return None
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as exc:
            self.problem(path, f"front matter is not valid YAML ({exc})")
            return None
        if not isinstance(meta, dict):
            self.problem(path, "front matter must be key: value lines")
            return None
        ok = True
        if not meta.get("title"):
            self.problem(path, "front matter needs 'title'")
            ok = False
        meta["date"] = as_date(meta.get("date"))
        if not meta["date"]:
            self.problem(path, "front matter needs 'date' as YYYY-MM-DD")
            ok = False
        body = text[match.end():]
        if not body.strip():
            self.problem(path, "has no content after the front matter")
            ok = False
        return (meta, body) if ok else None

    def check_links(self, path: Path, rendered: str) -> None:
        for url in HREF.findall(rendered):
            url = html.unescape(url)
            if external(url) and not self.allow.permits(url):
                what = ("that repository or page isn't" if is_shared((urlsplit(url).hostname or "").lower())
                        else "its host isn't")
                self.problem(path, f"links to {url}, but {what} listed in course/link-hosts.txt, "
                                   "course/cases.yaml or course/labs.yaml")

    def load_unit_content(self) -> dict[str, dict]:
        content = {}
        units_dir = self.root / "units"
        if not units_dir.is_dir():
            return content
        for folder in sorted(units_dir.iterdir()):
            if not folder.is_dir():
                self.problem(folder, "only unit folders belong in units/")
                continue
            unit = self.unit_by_slug.get(folder.name)
            if not unit:
                self.problem(folder, "folder name is not a unit slug from course/units.yaml")
                continue
            parts, present = {}, set()
            for path in sorted(folder.iterdir()):
                if path.name not in UNIT_PARTS:
                    self.problem(path, f"unexpected file; a unit folder holds only {', '.join(UNIT_PARTS)}")
                    continue
                present.add(path.name)
                parsed = self.read_markdown(path)
                if not parsed:
                    continue
                meta, body = parsed
                rendered = render_markdown(body, id_prefix=f"{path.stem}-", base_level=2)
                self.check_links(path, rendered)
                cases = meta.get("cases") or []
                for case in cases:
                    if case not in self.cases:
                        self.problem(path, f"cases: '{case}' is not in course/cases.yaml")
                    elif not self.cases[case].get("checked"):
                        self.problem(path, f"cases: '{case}' hasn't been checked in course/cases.yaml yet")
                parts[path.name] = {"title": str(meta["title"]), "date": meta["date"],
                                    "cases": cases, "html": rendered}
            missing = [name for name in REQUIRED_PARTS if name not in present]
            if missing:
                self.problem(folder, f"is missing {', '.join(missing)}")
            lab = self.labs[unit["lab"]]
            if not lab.get("checked"):
                self.problem(folder, f"uses lab '{lab['id']}', which hasn't been checked in course/labs.yaml yet")
            dates = [part["date"] for part in parts.values()]
            published = parts["lesson-1.md"]["date"] if "lesson-1.md" in parts else min(dates, default=None)
            content[unit["slug"]] = {"parts": parts, "published": published}
        return content

    def load_news(self) -> list[dict]:
        issues = []
        news_dir = self.root / "news"
        if not news_dir.is_dir():
            return issues
        for path in sorted(news_dir.iterdir()):
            if path.suffix != ".md" or not NEWS_NAME.fullmatch(path.stem):
                self.problem(path, "news files are named YYYY-Www.md, for example 2026-W45.md")
                continue
            parsed = self.read_markdown(path)
            if not parsed:
                continue
            meta, body = parsed
            units = meta.get("units") or []
            if not isinstance(units, list):
                self.problem(path, "units must be a list of unit slugs")
                units = []
            for slug in units:
                if slug not in self.unit_by_slug:
                    self.problem(path, f"units: '{slug}' is not in course/units.yaml")
            rendered = render_markdown(body)
            self.check_links(path, rendered)
            issues.append({
                "slug": path.stem,
                "title": str(meta["title"]),
                "date": meta["date"],
                "summary": str(meta.get("summary") or ""),
                "units": [slug for slug in units if slug in self.unit_by_slug],
                "html": rendered,
            })
        issues.sort(key=lambda issue: (issue["date"], issue["slug"]), reverse=True)
        return issues


def unit_states(units: list[dict], content: dict, progress: dict) -> dict[str, str]:
    """Each unit is done, low (done at confidence 1 or 2), current, published, or todo.

    The current unit is the first one whose lab you haven't logged.
    """
    states, current = {}, None
    for unit in units:
        slug = unit["slug"]
        entry = progress.get(slug)
        if entry and entry["lab_done"]:
            low = entry["confidence"] is not None and entry["confidence"] <= 2
            states[slug] = "low" if low else "done"
        elif current is None:
            current = slug
            states[slug] = "current"
        else:
            states[slug] = "published" if slug in content else "todo"
    return states


# Pages

def page(template: Template, *, title: str, body: str, root: str, description: str = "") -> str:
    return template.substitute(
        page_title=esc(title),
        site_title=esc(SITE_TITLE),
        description=esc(description or SITE_TITLE),
        root=root,
        body=body,
    )


def state_text(site: Site, slug: str) -> str:
    if site.states[slug] == "current" and slug not in site.content:
        return "Up next"
    return STATE_TEXT[site.states[slug]]


def status_chip(site: Site, slug: str) -> str:
    return f'<span class="status {site.states[slug]}">{state_text(site, slug)}</span>'


def current_unit(site: Site):
    return next((u for u in site.units if site.states[u["slug"]] == "current"), None)


def track_markup(site: Site, root: str, compact: bool) -> str:
    groups, module, cells = [], None, []
    for unit in site.units:
        if unit["module"] != module and cells:
            groups.append((module, cells))
            cells = []
        module = unit["module"]
        cells.append(f'<span class="cell {site.states[unit["slug"]]}" '
                     f'title="Unit {unit["number"]}: {esc(unit["title"])}"></span>')
    if cells:
        groups.append((module, cells))
    done = sum(state in ("done", "low") for state in site.states.values())
    summary = f"{done} of {len(site.units)} units done"
    now = current_unit(site)
    next_line = (f'Now: <a href="{root}units/{esc(now["slug"])}.html">'
                 f'Unit {now["number"]}, {esc(now["title"])}</a>' if now else "Course complete.")
    heading = f'<h2><a href="{root}course.html">Course</a></h2>' if compact else ""
    return (
        f'<section class="track{" compact" if compact else ""}" aria-label="{summary}">{heading}'
        '<div class="track-cells" aria-hidden="true">'
        + "".join(f'<div class="track-group" title="{esc(name)}">{"".join(group)}</div>' for name, group in groups)
        + f'</div><p class="track-caption"><strong>{summary}.</strong> {next_line}</p></section>'
    )


def lab_line(lab: dict) -> str:
    bits = [esc(lab["name"])] + [esc(lab[key]) for key in ("time", "cost") if lab.get(key)]
    return " · ".join(bits)


def unchecked_flag(entry: dict) -> str:
    return "" if entry.get("checked") else ' <span class="unchecked">not yet checked</span>'


def build_home(site: Site, template: Template) -> str:
    parts = []
    unit = current_unit(site)
    if unit:
        slug, link = unit["slug"], f'units/{esc(unit["slug"])}.html'
        lab = site.labs[unit["lab"]]
        dateline = (f'<p class="dateline">Unit {unit["number"]} of {len(site.units)} · '
                    f'{esc(unit["module"])}</p>')
        title = f'<h1><a href="{link}">{esc(unit["title"])}</a></h1>'
        if slug in site.content:
            steps = "".join(
                f'<li><a href="{link}#{name[:-3]}">{label}</a>: {esc(part["title"])}</li>'
                for name, label in UNIT_PARTS.items()
                if (part := site.content[slug]["parts"].get(name))
            )
            body = (f'<ol class="steps">{steps}</ol>'
                    f'<p class="meta">Lab: {lab_line(lab)}</p>'
                    "<p>When you finish the lab, log it in <code>me/progress.yaml</code>. "
                    "The next unit is published once it's there.</p>")
        else:
            body = ("<p class=\"summary\">This unit is up next. Its lessons appear after the "
                    "routine's next run; until then you can read the objectives and get the lab ready.</p>"
                    f'<p class="meta">Lab: {lab_line(lab)}</p>')
        objectives = "".join(f"<li>{esc(o)}</li>" for o in unit["objectives"])
        parts.append(f'<article class="latest">{dateline}{title}{body}'
                     f'<h2 class="small">By the end you can</h2><ul class="objectives">{objectives}</ul>'
                     f'<p><a class="read" href="{link}">Open the unit</a></p></article>')
    else:
        parts.append('<article class="latest"><h1>Course complete</h1>'
                     '<p class="summary">You have logged the lab for every unit.</p></article>')
    parts.append(track_markup(site, "", compact=True))
    if site.news:
        rows = "".join(
            f'<li><time datetime="{n["date"].isoformat()}">{nice_date(n["date"])}</time>'
            f'<a href="news/{esc(n["slug"])}.html">{esc(n["title"])}</a></li>'
            for n in site.news[:5]
        )
        parts.append(f'<section class="archive"><h2><a href="news.html">News</a></h2><ol>{rows}</ol></section>')
    return page(template, title=SITE_TITLE, body="".join(parts), root="",
                description="A self-paced security course: one unit a week, built around real incidents and a weekly lab.")


def build_course(site: Site, template: Template) -> str:
    sections, module, rows = [], None, []

    def close():
        if rows:
            sections.append(f'<section class="module"><h2>{esc(module)}</h2>'
                            f'<ol class="unit-list">{"".join(rows)}</ol></section>')

    for unit in site.units:
        if unit["module"] != module:
            close()
            module, rows = unit["module"], []
        slug = unit["slug"]
        rows.append(
            f'<li class="{site.states[slug]}"><span class="num">{unit["number"]}</span>'
            f'<div><a href="units/{esc(slug)}.html">{esc(unit["title"])}</a>'
            f'<p class="meta">Lab: {lab_line(site.labs[unit["lab"]])}</p></div>'
            f"{status_chip(site, slug)}</li>"
        )
    close()
    body = ('<article class="course-page"><h1>Course map</h1>'
            '<p class="summary">One unit a week, in this order. Each unit has two lessons built '
            "around a real incident, a lab, and a review. A unit counts as done once you log its lab "
            "in <code>me/progress.yaml</code>.</p>"
            f'{track_markup(site, "", compact=False)}{"".join(sections)}</article>')
    return page(template, title="Course map", body=body, root="")


def case_card(case: dict, root: str) -> str:
    cause = (f'<p class="meta"><strong>Root cause:</strong> {esc(case["root_cause"])}</p>'
             if case.get("root_cause") else "")
    return (f'<div class="case-card"><h3><a href="{root}cases.html#case-{esc(case["id"])}">'
            f'{esc(case["title"])}</a> <span class="year">{esc(case["year"])}</span>{unchecked_flag(case)}</h3>'
            f'<p>{esc(case["summary"])}</p>{cause}</div>')


def lab_facts(lab: dict) -> str:
    rows = [("Where", f'<a href="{esc(lab["url"])}" rel="noopener noreferrer">'
                      f'{esc(urlsplit(lab["url"]).hostname)}</a>, {LAB_KINDS[lab["kind"]]}')]
    for key, label in (("cost", "Cost"), ("time", "Time"), ("setup", "Before you start"),
                       ("do", "This week"), ("defender", "Defender's view")):
        if lab.get(key):
            rows.append((label, esc(lab[key])))
    if lab.get("extra"):
        links = "".join(f'<li><a href="{esc(e["url"])}" rel="noopener noreferrer">{esc(e["title"])}</a></li>'
                        for e in lab["extra"])
        rows.append(("Also useful", f"<ul>{links}</ul>"))
    return '<dl class="facts">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl>"


def attack_link(technique: str) -> str:
    url = f"https://attack.mitre.org/techniques/{technique.replace('.', '/')}/"
    return f'<a href="{url}" rel="noopener noreferrer">{esc(technique)}</a>'


def progress_markup(site: Site, slug: str) -> str:
    entry = site.progress.get(slug)
    if entry and entry["lab_done"]:
        confidence = f" Confidence {entry['confidence']} of 5." if entry["confidence"] else ""
        note = f'<blockquote><p>{esc(entry["note"])}</p></blockquote>' if entry["note"] else ""
        return f'<p>Lab done on {nice_date(entry["lab_done"])}.{confidence}</p>{note}'
    snippet = (f"  - unit: {slug}\n    lab_done: YYYY-MM-DD\n    confidence: 3\n"
               '    note: "one line on what stuck and what didn\'t"')
    return ("<p>Not logged yet. When you finish the lab, add this under <code>progress:</code> "
            f"in <code>me/progress.yaml</code>:</p><pre><code>{esc(snippet)}</code></pre>")


def build_unit(site: Site, unit: dict, template: Template) -> str:
    slug, root = unit["slug"], "../"
    parts = site.content.get(slug, {}).get("parts", {})
    sections, contents = [], []

    def add(ident: str, label: str, heading: str, inner: str) -> None:
        sections.append(f'<section id="{ident}" class="part"><h2>{heading}</h2>{inner}</section>')
        contents.append(f'<a href="#{ident}">{label}</a>')

    covers = "".join(f"<li>{esc(c)}</li>" for c in unit.get("covers") or [])
    attack = ", ".join(attack_link(t) for t in unit.get("attack") or [])
    add("objectives", "Objectives", "By the end you can",
        '<ul class="objectives">' + "".join(f"<li>{esc(o)}</li>" for o in unit["objectives"]) + "</ul>"
        + (f"<details><summary>Topics covered</summary><ul>{covers}</ul></details>" if covers else "")
        + (f'<p class="meta">MITRE ATT&amp;CK: {attack}</p>' if attack else ""))

    case_ids = list(dict.fromkeys((unit.get("cases") or []) + [c for p in parts.values() for c in p["cases"]]))
    if case_ids:
        add("cases", "Incidents", "Real incidents", "".join(case_card(site.cases[c], root) for c in case_ids))

    def add_part(name: str) -> None:
        part = parts[name]
        add(name[:-3], UNIT_PARTS[name], f"{UNIT_PARTS[name]}: {esc(part['title'])}",
            f'<p class="dateline"><time datetime="{part["date"].isoformat()}">{nice_date(part["date"])}</time></p>'
            f'<div class="prose">{part["html"]}</div>')

    for name in ("lesson-1.md", "lesson-2.md"):
        if name in parts:
            add_part(name)
    if not parts:
        sections.append('<p class="pending">The lessons for this unit appear when you reach it. '
                        "The objectives, incidents and lab below are already set.</p>")

    lab = site.labs[unit["lab"]]
    guide = ""
    if "lab.md" in parts:
        guide = f'<h3>Lab guide: {esc(parts["lab.md"]["title"])}</h3><div class="prose">{parts["lab.md"]["html"]}</div>'
    add("lab", "Lab", f"Lab: {esc(lab['name'])}{unchecked_flag(lab)}", lab_facts(lab) + guide)

    for name in ("review.md", "debrief.md"):
        if name in parts:
            add_part(name)

    add("progress", "Your progress", "Your progress", progress_markup(site, slug))

    mentions = [n for n in site.news if slug in n["units"]]
    if mentions:
        add("news", "In the news", "In the news", '<ul class="mentions">' + "".join(
            f'<li><a href="{root}news/{esc(n["slug"])}.html">{esc(n["title"])}</a> '
            f'<span class="meta">{nice_date(n["date"])}</span></li>' for n in mentions) + "</ul>")

    builds_on = ", ".join(f'<a href="{esc(b)}.html">{esc(site.unit_by_slug[b]["title"])}</a>'
                          for b in unit.get("builds_on") or [])
    index = unit["number"] - 1
    prev_link = (f'<a href="{esc(site.units[index - 1]["slug"])}.html">← Unit {index}</a>' if index else "<span></span>")
    next_link = (f'<a href="{esc(site.units[index + 1]["slug"])}.html">Unit {index + 2} →</a>'
                 if index + 1 < len(site.units) else "<span></span>")
    body = (
        '<article class="unit">'
        '<header class="post-head">'
        f'<p class="dateline">Unit {unit["number"]} of {len(site.units)} · {esc(unit["module"])} · {status_chip(site, slug)}</p>'
        f'<h1>{esc(unit["title"])}</h1>'
        + (f'<p class="concept">Builds on {builds_on}</p>' if builds_on else "")
        + f'<nav class="contents" aria-label="On this page">{"".join(contents)}</nav></header>'
        + "".join(sections)
        + f'<nav class="pager" aria-label="Units">{prev_link}<a href="{root}course.html">Course map</a>{next_link}</nav>'
        "</article>"
    )
    return page(template, title=unit["title"], body=body, root=root, description=unit["objectives"][0])


def build_cases(site: Site, template: Template) -> str:
    taught = {}
    for unit in site.units:
        lesson_cases = [c for p in site.content.get(unit["slug"], {}).get("parts", {}).values() for c in p["cases"]]
        for case in dict.fromkeys((unit.get("cases") or []) + lesson_cases):
            taught.setdefault(case, []).append(unit)
    entries = []
    for case in sorted(site.cases.values(), key=lambda c: (c["year"], c["title"])):
        helped = "".join(f"<li>{esc(h)}</li>" for h in case.get("would_have_helped") or [])
        sources = "".join(
            f'<li><span class="kind">{esc(s.get("kind", ""))}</span> '
            f'<a href="{esc(s["url"])}" rel="noopener noreferrer">{esc(s.get("title") or s["url"])}</a></li>'
            for s in case["sources"]
        )
        units = ", ".join(f'<a href="units/{esc(u["slug"])}.html">Unit {u["number"]}, {esc(u["title"])}</a>'
                          for u in taught.get(case["id"], []))
        checked = (f'<p class="meta">Checked against its sources on {nice_date(as_date(case["checked"]))}.</p>'
                   if case.get("checked") else "")
        entries.append(
            f'<section class="case" id="case-{esc(case["id"])}">'
            f'<h2>{esc(case["title"])} <span class="year">{esc(case["year"])}</span>{unchecked_flag(case)}</h2>'
            f'<p>{esc(case["summary"])}</p>'
            + (f'<p><strong>Root cause:</strong> {esc(case["root_cause"])}</p>' if case.get("root_cause") else "")
            + (f"<h3>What would have helped</h3><ul>{helped}</ul>" if helped else "")
            + f'<h3>Sources</h3><ul class="sources">{sources}</ul>'
            + (f'<p class="meta">Taught in {units}.</p>' if units else "")
            + checked + "</section>"
        )
    body = ('<article class="cases-page"><h1>Incident library</h1>'
            '<p class="summary">The real incidents the lessons are built on, oldest first. An entry marked '
            "“not yet checked” hasn't been read against its sources, and the routine won't use it until it has.</p>"
            + "".join(entries) + "</article>")
    return page(template, title="Incident library", body=body, root="")


def build_news_index(site: Site, template: Template) -> str:
    if site.news:
        rows = "".join(
            f'<li><time datetime="{n["date"].isoformat()}">{nice_date(n["date"])}</time>'
            f'<a href="news/{esc(n["slug"])}.html">{esc(n["title"])}</a></li>'
            for n in site.news
        )
        listing = f'<section class="archive"><ol>{rows}</ol></section>'
    else:
        listing = "<p>No news yet. The routine adds one page a week.</p>"
    body = ('<article><h1>News</h1><p class="summary">A short weekly round-up, with stories tied back to '
            f"the units they illustrate.</p>{listing}</article>")
    return page(template, title="News", body=body, root="")


def build_news(site: Site, issue: dict, template: Template) -> str:
    root = "../"
    units = ", ".join(f'<a href="{root}units/{esc(s)}.html">{esc(site.unit_by_slug[s]["title"])}</a>'
                      for s in issue["units"])
    body = (
        '<article class="post"><header class="post-head">'
        f'<p class="dateline"><time datetime="{issue["date"].isoformat()}">{nice_date(issue["date"])}</time></p>'
        f'<h1>{esc(issue["title"])}</h1>'
        + (f'<p class="concept">Connects to {units}</p>' if units else "")
        + f'</header><div class="prose">{issue["html"]}</div></article>'
    )
    return page(template, title=issue["title"], body=body, root=root, description=issue["summary"])


def build_feed(site: Site) -> str:
    base = SITE_URL or "."
    items = [
        (site.content[u["slug"]]["published"], f"Unit {u['number']}: {u['title']}",
         f"{base}/units/{u['slug']}.html", u["objectives"][0])
        for u in site.units if site.content.get(u["slug"], {}).get("published")
    ] + [(n["date"], n["title"], f"{base}/news/{n['slug']}.html", n["summary"]) for n in site.news]
    items.sort(key=lambda item: item[0], reverse=True)
    updated = items[0][0] if items else dt.date.today()
    entries = "".join(
        "<entry>"
        f"<title>{esc(title)}</title>"
        f'<link href="{esc(url)}"/>'
        f"<id>{esc(url)}</id>"
        f"<updated>{day.isoformat()}T07:00:00Z</updated>"
        f"<summary>{esc(summary)}</summary>"
        "</entry>"
        for day, title, url, summary in items[:30]
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        f"<title>{esc(SITE_TITLE)}</title>"
        f'<link href="{esc(base)}/"/>'
        f'<link rel="self" href="{esc(base)}/feed.xml"/>'
        f"<id>{esc(base)}/</id>"
        f"<updated>{updated.isoformat()}T07:00:00Z</updated>"
        f"<author><name>{esc(SITE_TITLE)}</name></author>"
        f"{entries}</feed>\n"
    )


def build_site(root: Path, out: Path) -> Site:
    site = Site(root)
    template = Template((root / "theme" / "base.html").read_text(encoding="utf-8"))
    if out.exists():
        shutil.rmtree(out)
    (out / "units").mkdir(parents=True)
    (out / "news").mkdir()
    shutil.copy(root / "theme" / "style.css", out / "style.css")

    def write(path: str, text: str) -> None:
        (out / path).write_text(text, encoding="utf-8")

    write("index.html", build_home(site, template))
    write("course.html", build_course(site, template))
    write("cases.html", build_cases(site, template))
    write("news.html", build_news_index(site, template))
    for unit in site.units:
        write(f"units/{unit['slug']}.html", build_unit(site, unit, template))
    for issue in site.news:
        write(f"news/{issue['slug']}.html", build_news(site, issue, template))
    write("feed.xml", build_feed(site))
    return site


def main() -> int:
    try:
        site = build_site(ROOT, ROOT / "_site")
    except BuildError as exc:
        print(f"Build failed with {len(exc.problems)} problem(s):", file=sys.stderr)
        for problem in exc.problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"Built {len(site.units)} unit pages ({len(site.content)} with lessons), "
          f"{len(site.news)} news page(s) and the incident library into _site/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
