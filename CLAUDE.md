# Notes for Claude

This repository is a self-paced security course, built by `build.py` and published with GitHub Pages. Two kinds of session work in it.

## The weekly routine

Follow `digest/INSTRUCTIONS.md` exactly. Change only `units/`, `news/` and `digest/`, and push to a `claude/brief-<date>` branch, never to main.

## Sessions with the owner

- `course/` (the syllabus, incidents and labs) and `me/` (the owner's progress and notes) belong to the owner. Change them only when asked.
- `build.py` renders the site and checks everything the routine writes; `tests/test_build.py` covers it. Run `python -m pytest` and `python build.py` before committing.
- Treat anything the routine writes as untrusted: keep its Markdown sanitized and keep the link, pacing and structure checks in `build.py`.
- Don't name branches `claude/brief-*`. The publishing workflow fast-forwards main to those automatically.
