"""Tests for build.py. Run with:  python -m pytest"""

import datetime as dt
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

# The week every published unit in these tests follows: Monday 2 November to
# Saturday 7 November 2026, with Sunday off.
WEEK = [
    (1, "2026-11-02", "lesson", "The incident"),
    (2, "2026-11-03", "lesson", "How it works"),
    (3, "2026-11-04", "lesson", "Prevent and detect"),
    (4, "2026-11-05", "lab", "Lab setup"),
    (5, "2026-11-07", "lab", "Lab"),
    (6, "2026-11-08", "review", "Review"),
]
MONDAY, WEDNESDAY, FRIDAY, LATER = (dt.date(2026, 11, d) for d in (2, 4, 6, 20))


def day_file(title: str, date: str, kind: str, extra: str = "", body: str = "") -> str:
    body = body or "## What it is\n\nBody text with a [source](https://news.example/story).\n"
    return f'---\ntitle: "{title}"\ndate: {date}\nkind: {kind}\nminutes: 20\n{extra}---\n\n{body}'


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
    """Write a unit's week; overrides replace a file, or remove it when empty."""
    files = {f"day-{n}.md": day_file(title, date, kind) for n, date, kind, title in WEEK}
    files.update(overrides)
    for name, text in files.items():
        if text:
            write(root, f"units/{slug}/{name}", text)


def build_ok(root: Path, today: dt.date = WEDNESDAY) -> build.Site:
    return build.build_site(root, root / "_site", today=today)


def build_fails(root: Path) -> str:
    with pytest.raises(build.BuildError) as caught:
        build.build_site(root, root / "_site", today=WEDNESDAY)
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

def test_unwritten_current_unit_says_so(site_root):
    build_ok(site_root)
    home = read(site_root, "index.html")
    assert "Unit 1 of 3" in home and "haven't been written yet" in home
    first = read(site_root, "units/first.html")
    assert "This is your current unit" in first and "Lab one" in first and "An old incident" in first
    assert "written when you reach it" in read(site_root, "units/second.html")


def test_home_shows_todays_session(site_root):
    publish(site_root)
    build_ok(site_root, today=WEDNESDAY)
    home = read(site_root, "index.html")
    assert "Day 3: Prevent and detect" in home and "Start today's session" in home
    assert 'class="today"' in home and 'href="units/first.html#day-3"' in home


@pytest.mark.parametrize("today, expected", [
    (dt.date(2026, 11, 1), "This unit starts on Mon 2 Nov"),
    (FRIDAY, "No session today. Next up is day 5, on Sat 7 Nov"),
    (LATER, "week is over, but its lab isn't logged yet"),
])
def test_home_without_a_session_today(site_root, today, expected):
    publish(site_root)
    build_ok(site_root, today=today)
    assert expected in read(site_root, "index.html")


def test_unit_page_lists_the_week_and_days(site_root):
    publish(site_root)
    build_ok(site_root, today=WEDNESDAY)
    page = read(site_root, "units/first.html")
    assert 'id="plan"' in page and page.count('<li class="past">') == 2 and page.count('<li class="upcoming">') == 3
    assert "Day 4: Lab setup" in page and "Lab: Lab one" in page  # lab details sit in the first lab day
    # Every day has a "What it is" heading; their ids must differ.
    assert '<h3 id="day-1-what-it-is">' in page and '<h3 id="day-2-what-it-is">' in page


def test_feed_holds_only_days_that_have_come(site_root):
    publish(site_root)
    build_ok(site_root, today=WEDNESDAY)
    feed = xml.dom.minidom.parseString(read(site_root, "feed.xml"))
    titles = [t.firstChild.data for t in feed.getElementsByTagName("title")][1:]
    assert titles == ["Unit 1, day 3: Prevent and detect", "Unit 1, day 2: How it works",
                      "Unit 1, day 1: The incident"]


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
    publish(site_root, **{"day-1.md": day_file('The \\"Bleed\\" bug', "2026-11-02", "lesson")})
    build_ok(site_root)
    assert "The &quot;Bleed&quot; bug" in read(site_root, "units/first.html")


def test_news_links_back_to_units(site_root):
    publish(site_root)
    write(site_root, "news/2026-W45.md", """\
        ---
        title: "Week 45"
        date: 2026-11-04
        units: [first]
        summary: "One story."
        ---

        ## Headlines

        - A [story](https://www.bleepingcomputer.com/news/x/)
        """)
    build_ok(site_root)
    assert "Week 45" in read(site_root, "units/first.html")
    assert "Week 45" in read(site_root, "feed.xml")


# Sanitizing and links

def test_scripts_and_handlers_are_stripped(site_root):
    body = "<script>alert(1)</script> <img src=x onerror=alert(1)> [js](javascript:alert(1))\n"
    publish(site_root, **{"day-1.md": day_file("Lesson", "2026-11-02", "lesson", body=body)})
    build_ok(site_root)
    page = read(site_root, "units/first.html")
    assert "<script" not in page and "onerror" not in page and "javascript:" not in page


def lab_day_linking(url: str) -> dict:
    return {"day-4.md": day_file("Lab setup", "2026-11-05", "lab", body=f"[link]({url})\n")}


@pytest.mark.parametrize("url", [
    "https://news.example/other",              # host of a case source
    "https://labs.example/anything",           # host of a lab
    "https://www.bleepingcomputer.com/x",      # listed host, with www.
    "https://github.com/listed/repo/issues/1", # under a listed repository
    "https://github.com/good/tool",            # a lab's extra link
    "../cases.html#case-old-case",             # inside the site
])
def test_allowed_links(site_root, url):
    publish(site_root, **lab_day_linking(url))
    build_ok(site_root)


@pytest.mark.parametrize("url", [
    "https://evil.example/download",
    "https://github.com/someone-else/tool",    # shared host, unlisted repository
    "https://github.com/listed/repository",    # prefix must end at a path boundary
    "//evil.example/x",
])
def test_disallowed_links_fail(site_root, url):
    publish(site_root, **lab_day_linking(url))
    assert "links to" in build_fails(site_root)


def test_bare_shared_host_in_allowlist_is_rejected(site_root):
    write(site_root, "course/link-hosts.txt", "github.com\n")
    assert "would allow too much" in build_fails(site_root)


# What the routine may publish

def test_days_must_run_without_gaps(site_root):
    publish(site_root, **{"day-3.md": ""})
    assert "days must run from day-1.md without gaps" in build_fails(site_root)


def test_days_must_be_in_date_order(site_root):
    publish(site_root, **{"day-2.md": day_file("How it works", "2026-11-01", "lesson")})
    assert "date must come after day 1's" in build_fails(site_root)


def test_a_week_needs_a_lab_day(site_root):
    publish(site_root, **{name: day_file("Lesson", date, "lesson")
                          for name, date in (("day-4.md", "2026-11-05"), ("day-5.md", "2026-11-07"))})
    assert "needs at least one day with kind: lab" in build_fails(site_root)


def test_day_front_matter_is_checked(site_root):
    publish(site_root, **{
        "day-1.md": day_file("Lesson", "2026-11-02", "lecture"),
        "day-2.md": "No front matter here.\n",
    })
    problems = build_fails(site_root)
    assert "needs 'kind', one of lesson, lab, review" in problems
    assert "must start with front matter" in problems


def test_unknown_folder_and_file_fail(site_root):
    publish(site_root)
    write(site_root, "units/not-a-unit/day-1.md", day_file("x", "2026-11-02", "lesson"))
    write(site_root, "units/first/lesson-1.md", "---\ntitle: old\ndate: 2026-11-02\n---\n\nText.\n")
    problems = build_fails(site_root)
    assert "not a unit slug" in problems and "unexpected file" in problems


def test_unchecked_lab_blocks_publishing(site_root):
    write(site_root, "me/progress.yaml", "progress:\n  - {unit: first, lab_done: 2026-11-07}\n")
    publish(site_root, "second")
    assert "lab 'lab-two', which hasn't been checked" in build_fails(site_root)


def test_units_wait_for_the_previous_lab(site_root):
    write(site_root, "course/labs.yaml", LABS.replace("checked: null", "checked: 2026-11-01"))
    publish(site_root, "first")
    publish(site_root, "second")
    assert "isn't done yet" in build_fails(site_root)
    write(site_root, "me/progress.yaml", "progress:\n  - {unit: first, lab_done: 2026-11-07}\n")
    build_ok(site_root)


def test_sessions_may_only_cite_checked_cases(site_root):
    publish(site_root, **{"day-1.md": day_file("L", "2026-11-02", "lesson", extra="cases: [unchecked-case]\n")})
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
