"""Tests for build.py. Run with:  python -m pytest"""

import shutil
import textwrap
import xml.dom.minidom
from pathlib import Path

import pytest

import build

REPO = Path(__file__).resolve().parent.parent

UNITS = """\
units:
  - slug: first
    module: Basics
    title: "First unit"
    objectives: ["Explain the first thing"]
    cases: [old-case]
    lab: lab-one
  - slug: second
    module: Basics
    title: "Second unit"
    objectives: ["Explain the second thing"]
    builds_on: [first]
    attack: [T1190, T1552.005]
    lab: lab-two
  - slug: third
    module: Web
    title: "Third unit"
    objectives: ["Explain the third thing"]
    lab: lab-two
"""

CASES = """\
cases:
  - id: old-case
    title: "An old incident"
    year: 2001
    summary: "Something happened."
    sources:
      - {kind: press, title: "Report", url: "https://news.example/story"}
    checked: 2026-11-01
  - id: unchecked-case
    title: "A newer incident"
    year: 2020
    summary: "Something else happened."
    sources:
      - {kind: research, title: "Write-up", url: "https://github.com/someone/writeup"}
    checked: null
"""

LABS = """\
labs:
  - id: lab-one
    name: "Lab one"
    kind: platform
    url: https://labs.example/one
    cost: free
    extra:
      - {title: "A tool", url: "https://github.com/good/tool"}
    checked: 2026-11-01
  - id: lab-two
    name: "Lab two"
    kind: own-lab
    url: https://labs.example/two
    checked: null
"""

LESSON = """\
---
title: "{title}"
date: 2026-11-02
---

## What it is

Body text with a [source](https://news.example/story).
"""


@pytest.fixture
def site_root(tmp_path: Path) -> Path:
    """A small, valid course with no published units yet."""
    root = tmp_path / "repo"
    shutil.copytree(REPO / "theme", root / "theme")
    write(root, "course/units.yaml", UNITS)
    write(root, "course/cases.yaml", CASES)
    write(root, "course/labs.yaml", LABS)
    write(root, "course/link-hosts.txt", "# news\nbleepingcomputer.com\nhttps://github.com/listed/repo\n")
    return root


def write(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


def publish(root: Path, slug: str = "first", **overrides: str) -> None:
    """Write a complete unit folder; overrides replace (or, if empty, remove) a part."""
    files = {name: LESSON.format(title=f"{label} title") for name, label in
             (("lesson-1.md", "Lesson 1"), ("lesson-2.md", "Lesson 2"), ("lab.md", "Lab guide"))}
    files.update(overrides)
    for name, text in files.items():
        if text:
            write(root, f"units/{slug}/{name}", text)


def build_ok(root: Path) -> build.Site:
    return build.build_site(root, root / "_site")


def build_fails(root: Path) -> str:
    with pytest.raises(build.BuildError) as caught:
        build.build_site(root, root / "_site")
    return "\n".join(caught.value.problems)


def read(root: Path, name: str) -> str:
    return (root / "_site" / name).read_text(encoding="utf-8")


# The real repository

def test_real_course_builds(tmp_path):
    site = build.build_site(REPO, tmp_path / "out")
    assert len(site.units) == len(list((tmp_path / "out" / "units").glob("*.html")))
    for page in ("index.html", "course.html", "cases.html", "news.html", "feed.xml"):
        assert (tmp_path / "out" / page).exists()


# Pages

def test_fresh_course_points_at_first_unit(site_root):
    build_ok(site_root)
    home = read(site_root, "index.html")
    assert "Unit 1 of 3" in home and "is up next" in home
    unit = read(site_root, "units/first.html")
    assert "appear when you reach it" in unit
    assert "An old incident" in unit and "Lab one" in unit


def test_published_unit_shows_lessons_with_distinct_ids(site_root):
    publish(site_root)
    build_ok(site_root)
    page = read(site_root, "units/first.html")
    assert "Lesson 1: Lesson 1 title" in page and "Lab guide: Lab guide title" in page
    # Both lessons have a "What it is" heading; their ids must differ.
    assert 'id="lesson-1-what-it-is"' in page and 'id="lesson-2-what-it-is"' in page
    assert '<h3 id="lesson-1-what-it-is">' in page  # shifted below the section's h2


def test_progress_moves_the_current_unit(site_root):
    write(site_root, "me/progress.yaml", """\
        progress:
          - unit: first
            lab_done: 2026-11-08
            confidence: 2
            note: "shaky on the details"
        """)
    site = build_ok(site_root)
    assert site.states == {"first": "low", "second": "current", "third": "todo"}
    assert "Unit 2 of 3" in read(site_root, "index.html")
    assert "shaky on the details" in read(site_root, "units/first.html")


def test_attack_ids_link_to_mitre(site_root):
    build_ok(site_root)
    assert 'href="https://attack.mitre.org/techniques/T1552/005/"' in read(site_root, "units/second.html")


def test_front_matter_quotes_are_parsed_properly(site_root):
    publish(site_root, **{"lesson-1.md": '---\ntitle: "The \\"Bleed\\" bug"\ndate: 2026-11-02\n---\n\nText.\n'})
    build_ok(site_root)
    assert "The &quot;Bleed&quot; bug" in read(site_root, "units/first.html")


def test_news_links_back_to_units_and_feed_is_valid(site_root):
    publish(site_root)
    write(site_root, "news/2026-W45.md", """\
        ---
        title: "Week 45"
        date: 2026-11-08
        units: [first]
        summary: "One story."
        ---

        ## Headlines

        - A [story](https://www.bleepingcomputer.com/news/x/)
        """)
    build_ok(site_root)
    assert "Week 45" in read(site_root, "units/first.html")
    feed = xml.dom.minidom.parseString(read(site_root, "feed.xml"))
    titles = [t.firstChild.data for t in feed.getElementsByTagName("title")]
    assert "Week 45" in titles and "Unit 1: First unit" in titles


# Sanitizing and links

def test_scripts_and_handlers_are_stripped(site_root):
    publish(site_root, **{"lesson-1.md": (
        "---\ntitle: Lesson\ndate: 2026-11-02\n---\n\n"
        "<script>alert(1)</script> <img src=x onerror=alert(1)> [js](javascript:alert(1))\n")})
    build_ok(site_root)
    page = read(site_root, "units/first.html")
    assert "<script" not in page and "onerror" not in page and "javascript:" not in page


@pytest.mark.parametrize("url", [
    "https://news.example/other",              # host of a case source
    "https://labs.example/anything",           # host of a lab
    "https://www.bleepingcomputer.com/x",      # listed host, with www.
    "https://github.com/listed/repo/issues/1", # under a listed repository
    "https://github.com/good/tool",            # a lab's extra link
    "../cases.html#case-old-case",             # inside the site
])
def test_allowed_links(site_root, url):
    publish(site_root, **{"lab.md": f"---\ntitle: Lab\ndate: 2026-11-02\n---\n\n[link]({url})\n"})
    build_ok(site_root)


@pytest.mark.parametrize("url", [
    "https://evil.example/download",
    "https://github.com/someone-else/tool",    # shared host, unlisted repository
    "https://github.com/listed/repository",    # prefix must end at a path boundary
    "//evil.example/x",
])
def test_disallowed_links_fail(site_root, url):
    publish(site_root, **{"lab.md": f"---\ntitle: Lab\ndate: 2026-11-02\n---\n\n[link]({url})\n"})
    assert "links to" in build_fails(site_root)


def test_bare_shared_host_in_allowlist_is_rejected(site_root):
    write(site_root, "course/link-hosts.txt", "github.com\n")
    assert "would allow too much" in build_fails(site_root)


# What the routine may publish

def test_unit_folder_must_be_complete(site_root):
    publish(site_root, **{"lab.md": ""})
    assert "is missing lab.md" in build_fails(site_root)


def test_unknown_folder_and_file_fail(site_root):
    publish(site_root)
    write(site_root, "units/not-a-unit/lesson-1.md", LESSON.format(title="x"))
    write(site_root, "units/first/extra.html", "<script></script>")
    problems = build_fails(site_root)
    assert "not a unit slug" in problems and "unexpected file" in problems


def test_front_matter_is_required(site_root):
    publish(site_root, **{"lesson-2.md": "No front matter here.\n"})
    assert "must start with front matter" in build_fails(site_root)


def test_unchecked_lab_blocks_publishing(site_root):
    publish(site_root, "second")
    assert "lab 'lab-two', which hasn't been checked" in build_fails(site_root)


def test_lessons_may_only_cite_checked_cases(site_root):
    publish(site_root, **{"lesson-1.md": "---\ntitle: L\ndate: 2026-11-02\ncases: [unchecked-case]\n---\n\nText.\n"})
    assert "'unchecked-case' hasn't been checked" in build_fails(site_root)


def test_news_must_name_real_units(site_root):
    write(site_root, "news/2026-W45.md", "---\ntitle: W\ndate: 2026-11-08\nunits: [nope]\n---\n\nText.\n")
    write(site_root, "news/latest.md", "---\ntitle: W\ndate: 2026-11-08\n---\n\nText.\n")
    problems = build_fails(site_root)
    assert "'nope' is not in course/units.yaml" in problems and "named YYYY-Www.md" in problems


# Your files

def test_progress_is_validated(site_root):
    write(site_root, "me/progress.yaml", """\
        progress:
          - {unit: first, lab_done: someday, confidence: 7}
          - {unit: missing}
        """)
    problems = build_fails(site_root)
    assert "lab_done must be a date" in problems
    assert "confidence must be a whole number" in problems
    assert "'missing' is not in course/units.yaml" in problems


@pytest.mark.parametrize("value", ["yes", "true", "done"])
def test_checked_must_be_a_date(site_root, value):
    write(site_root, "course/labs.yaml", LABS.replace("checked: 2026-11-01", f"checked: {value}"))
    assert "must be the date you checked it" in build_fails(site_root)


def test_course_references_are_validated(site_root):
    write(site_root, "course/units.yaml", UNITS.replace("lab: lab-one", "lab: nope").replace("[first]", "[third]"))
    problems = build_fails(site_root)
    assert "lab 'nope' is not in course/labs.yaml" in problems
    assert "builds_on 'third' is not an earlier unit" in problems
