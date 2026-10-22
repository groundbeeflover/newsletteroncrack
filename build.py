#!/usr/bin/env python3
"""Build the security brief site into _site/.

Reads posts/*.md (front matter + Markdown) and digest/curriculum.md, renders
them to static HTML, sanitizes everything that came from Markdown, and writes
an Atom feed. Run locally with:  python build.py && python -m http.server -d _site
"""

import datetime as dt
import html
import os
import re
import shutil
import sys
from pathlib import Path
from string import Template

import markdown
import nh3

ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "posts"
CURRICULUM = ROOT / "digest" / "curriculum.md"
THEME = ROOT / "theme"
OUT = ROOT / "_site"

SITE_TITLE = os.environ.get("SITE_TITLE", "Daily security brief")
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")  # set by the deploy workflow

# Markdown is written by an agent that reads untrusted web content, so the
# rendered HTML is sanitized: no scripts, no event handlers, no inline styles,
# no javascript: URLs. Only what a written report needs survives.
ALLOWED_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "code", "dd", "del", "details", "div",
    "dl", "dt", "em", "h2", "h3", "h4", "hr", "i", "kbd", "li", "ol", "p", "pre",
    "s", "strong", "sub", "summary", "sup", "table", "tbody", "td", "th", "thead",
    "tr", "ul",
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
REQUIRED_FIELDS = ("title", "date")


class BuildError(Exception):
    pass


def parse_front_matter(text: str, source: Path) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise BuildError(f"{source.name}: missing front matter (file must start with ---)")
    parts = text.split("\n---", 1)
    if len(parts) != 2:
        raise BuildError(f"{source.name}: front matter is not closed with ---")
    meta = {}
    for line in parts[0].splitlines()[1:]:
        if not line.strip():
            continue
        if ":" not in line:
            raise BuildError(f"{source.name}: bad front matter line: {line!r}")
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[key.strip()] = value
    for field in REQUIRED_FIELDS:
        if not meta.get(field):
            raise BuildError(f"{source.name}: front matter needs '{field}'")
    try:
        meta["date"] = dt.date.fromisoformat(meta["date"])
    except ValueError as exc:
        raise BuildError(f"{source.name}: date must be YYYY-MM-DD") from exc
    try:
        meta["issue"] = int(meta.get("issue", 0))
    except ValueError as exc:
        raise BuildError(f"{source.name}: issue must be a number") from exc
    body = parts[1].split("\n", 1)[1] if "\n" in parts[1] else ""
    return meta, body


def render_markdown(text: str) -> str:
    rendered = markdown.markdown(
        text,
        extensions=["extra", "sane_lists", "toc"],
        extension_configs={"toc": {"permalink": False}},
        output_format="html",
    )
    clean = nh3.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )
    # Let wide tables scroll inside their own box on small screens.
    clean = clean.replace("<table>", '<div class="table-wrap"><table>')
    return clean.replace("</table>", "</table></div>")


def load_posts() -> list[dict]:
    posts = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"), path)
        meta["slug"] = path.stem
        meta["html"] = render_markdown(body)
        posts.append(meta)
    posts.sort(key=lambda p: (p["date"], p["issue"]), reverse=True)
    return posts


ITEM_RE = re.compile(r"^- \[( |x|X)\] (.+?)(?:\s+—\s+(\d{4}-\d{2}-\d{2}))?\s*$")


def load_curriculum() -> list[dict]:
    """Return [{'name': module, 'items': [{'title', 'done', 'date'}]}]."""
    modules = []
    if not CURRICULUM.exists():
        return modules
    for line in CURRICULUM.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            modules.append({"name": line[3:].strip(), "items": []})
            continue
        match = ITEM_RE.match(line.strip())
        if match and modules:
            modules[-1]["items"].append({
                "title": match.group(2).strip(),
                "done": match.group(1).lower() == "x",
                "date": match.group(3) or "",
            })
    return modules


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def nice_date(day: dt.date) -> str:
    return f"{day.day} {day.strftime('%B %Y')}"


def page(template: Template, *, title: str, body: str, root: str, description: str = "") -> str:
    return template.substitute(
        page_title=esc(title),
        site_title=esc(SITE_TITLE),
        description=esc(description or SITE_TITLE),
        root=root,
        body=body,
    )


def track_markup(modules: list[dict], root: str, compact: bool) -> str:
    items = [item for module in modules for item in module["items"]]
    if not items:
        return ""
    done = sum(item["done"] for item in items)
    upcoming = next((item for item in items if not item["done"]), None)
    groups = []
    for module in modules:
        cells = []
        for item in module["items"]:
            state = "done" if item["done"] else ("next" if item is upcoming else "todo")
            cells.append(f'<span class="cell {state}" title="{esc(item["title"])}"></span>')
        groups.append(
            f'<div class="track-group" title="{esc(module["name"])}">' + "".join(cells) + "</div>"
        )
    next_line = (
        f'Next up: <a href="{root}track.html">{esc(upcoming["title"])}</a>'
        if upcoming else "Track complete."
    )
    summary = f"{done} of {len(items)} concepts covered"
    css = "track compact" if compact else "track"
    heading = f'<h2><a href="{root}track.html">Learning track</a></h2>' if compact else ""
    return (
        f'<section class="{css}" aria-label="{summary}">{heading}'
        '<div class="track-cells" aria-hidden="true">' + "".join(groups) + "</div>"
        f'<p class="track-caption"><strong>{summary}.</strong> {next_line}</p>'
        f"</section>"
    )


def build_index(posts, modules, template) -> str:
    parts = []
    if posts:
        latest = posts[0]
        slug = esc(latest["slug"])
        issue = f', issue {latest["issue"]}' if latest["issue"] else ""
        concept = f'<p class="concept">Concept: {esc(latest["concept"])}</p>' if latest.get("concept") else ""
        summary = f'<p class="summary">{esc(latest["summary"])}</p>' if latest.get("summary") else ""
        parts.append(
            '<article class="latest">'
            f'<p class="dateline"><time datetime="{latest["date"].isoformat()}">{nice_date(latest["date"])}</time>{issue}</p>'
            f'<h1><a href="posts/{slug}.html">{esc(latest["title"])}</a></h1>'
            f"{concept}{summary}"
            f'<p><a class="read" href="posts/{slug}.html">Read today’s issue</a></p>'
            "</article>"
        )
    else:
        parts.append('<article class="latest"><h1>No issues yet</h1>'
                     "<p>The first issue appears here after the routine’s first run.</p></article>")
    parts.append(track_markup(modules, "", compact=True))
    if len(posts) > 1:
        rows = "".join(
            f'<li><time datetime="{p["date"].isoformat()}">{nice_date(p["date"])}</time>'
            f'<a href="posts/{esc(p["slug"])}.html">{esc(p["title"])}</a></li>'
            for p in posts[1:]
        )
        parts.append(f'<section class="archive"><h2>Earlier issues</h2><ol>{rows}</ol></section>')
    return page(template, title=SITE_TITLE, body="".join(parts), root="",
                description="A daily cybersecurity brief: news, market moves, and one concept to learn.")


def build_post(post, template) -> str:
    concept = (
        f'<p class="concept">Concept: <a href="../track.html">{esc(post["concept"])}</a></p>'
        if post.get("concept") else ""
    )
    issue = f', issue {post["issue"]}' if post["issue"] else ""
    body = (
        '<article class="post">'
        '<header class="post-head">'
        f'<p class="dateline"><time datetime="{post["date"].isoformat()}">{nice_date(post["date"])}</time>{issue}</p>'
        f'<h1>{esc(post["title"])}</h1>{concept}</header>'
        f'<div class="prose">{post["html"]}</div>'
        "</article>"
    )
    return page(template, title=post["title"], body=body, root="../",
                description=post.get("summary", ""))


def build_track(modules, template) -> str:
    sections = []
    for module in modules:
        rows = []
        for item in module["items"]:
            state = "done" if item["done"] else "todo"
            when = f'<time datetime="{item["date"]}">{item["date"]}</time>' if item["date"] else ""
            covered = '<span class="sr-only"> (covered)</span>' if item["done"] else ""
            rows.append(f'<li class="{state}"><span class="tick" aria-hidden="true"></span>'
                        f'<span class="item-title">{esc(item["title"])}{covered}</span>{when}</li>')
        done = sum(i["done"] for i in module["items"])
        sections.append(
            f'<section class="module"><h2>{esc(module["name"])}</h2>'
            f'<p class="module-count">{done} of {len(module["items"])}</p>'
            '<ul class="items">' + "".join(rows) + "</ul></section>"
        )
    body = (
        '<article class="track-page"><h1>Learning track</h1>'
        "<p class=summary>The routine covers these in order, one per issue. "
        "Add a topic to <code>digest/requests.md</code> to jump the queue.</p>"
        f"{track_markup(modules, '', compact=False)}{''.join(sections)}</article>"
    )
    return page(template, title="Learning track", body=body, root="")


def build_feed(posts) -> str:
    base = SITE_URL or "."
    updated = posts[0]["date"] if posts else dt.date.today()
    entries = []
    for post in posts[:30]:
        url = f"{base}/posts/{post['slug']}.html"
        stamp = f"{post['date'].isoformat()}T07:00:00Z"
        entries.append(
            "<entry>"
            f"<title>{esc(post['title'])}</title>"
            f'<link href="{esc(url)}"/>'
            f"<id>{esc(url)}</id>"
            f"<updated>{stamp}</updated>"
            f"<summary>{esc(post.get('summary', ''))}</summary>"
            f'<content type="html">{esc(post["html"])}</content>'
            "</entry>"
        )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        f"<title>{esc(SITE_TITLE)}</title>"
        f'<link href="{esc(base)}/"/>'
        f'<link rel="self" href="{esc(base)}/feed.xml"/>'
        f"<id>{esc(base)}/</id>"
        f"<updated>{updated.isoformat()}T07:00:00Z</updated>"
        f"{''.join(entries)}</feed>\n"
    )


def main() -> int:
    try:
        posts = load_posts()
        modules = load_curriculum()
    except BuildError as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1

    template = Template((THEME / "base.html").read_text(encoding="utf-8"))
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True)
    shutil.copy(THEME / "style.css", OUT / "style.css")

    (OUT / "index.html").write_text(build_index(posts, modules, template), encoding="utf-8")
    (OUT / "track.html").write_text(build_track(modules, template), encoding="utf-8")
    for post in posts:
        (OUT / "posts" / f"{post['slug']}.html").write_text(build_post(post, template), encoding="utf-8")
    (OUT / "feed.xml").write_text(build_feed(posts), encoding="utf-8")

    print(f"Built {len(posts)} issue(s) and the track page into {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
