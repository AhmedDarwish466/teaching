#!/usr/bin/env python3
"""Build the static teaching website from data/courses.json.

Usage:  python3 build.py
Output: site/  (index.html, courses/*.html, assets/style.css)

To add a lecture: append ["Title", "<Google Drive file id>"] to a course's
"lectures" list in data/courses.json and run the script again.
"""
import json, html, shutil
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "site"
data = json.loads((ROOT / "data" / "courses.json").read_text(encoding="utf-8"))
I = data["instructor"]
COURSES = data["courses"]
esc = html.escape


def drive_url(kind, fid):
    if kind == "folder":
        return f"https://drive.google.com/drive/folders/{fid}"
    if kind == "doc":
        return f"https://docs.google.com/document/d/{fid}/view"
    return f"https://drive.google.com/file/d/{fid}/view"


KIND_LABEL = {"sheet": "Problems", "cfd": "CFD", "video": "Video", "folder": "Folder",
              "reading": "Reading", "vocab": "Vocabulary"}

LOGO = """<svg class="logo" viewBox="0 0 40 40" aria-hidden="true">
<line x1="6" y1="5" x2="6" y2="35"/><line x1="34" y1="5" x2="34" y2="35"/>
<path d="M6 8 Q30 20 6 32" fill="none"/>
<g class="arrows"><line x1="6" y1="14" x2="18" y2="14"/><line x1="6" y1="20" x2="22" y2="20"/><line x1="6" y1="26" x2="18" y2="26"/></g>
</svg>"""


def page(title, body, depth=0, accent=None):
    up = "../" * depth
    style = f' style="--course:{accent}"' if accent else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="Teaching material by {esc(I['name'])}: lecture slides, problem sheets and projects.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,500..800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Arabic:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body{style}>
<header class="topbar">
  <a class="brand" href="{up}index.html">{LOGO}<span>{esc(I['name'])}</span></a>
  <nav aria-label="Main"><a href="{up}index.html#courses">Courses</a><a href="{up}index.html#about">About</a></nav>
</header>
{body}
<footer class="foot">
  <p>{esc(I['name'])} · {esc(I['title'])}</p>
  <p class="muted">Lecture files open in Google Drive.</p>
</footer>
</body>
</html>
"""


def count_items(c):
    n = len(c.get("resources", []))
    for _, items in c.get("resource_groups", []):
        n += len(items)
    return n


def index():
    groups = {}
    for c in COURSES:
        groups.setdefault(c["group"], []).append(c)
    total_lec = sum(len(c["lectures"]) for c in COURSES)
    total_res = sum(count_items(c) for c in COURSES)
    rows = []
    for g, cs in groups.items():
        items = []
        for c in cs:
            n = len(c["lectures"])
            meta = f"{n} lectures" if n else f"{count_items(c)} material sets"
            ar = f'<span class="ar" lang="ar" dir="rtl">{esc(c["title_ar"])}</span>' if c.get("title_ar") else ""
            items.append(f"""<li><a class="course-row" href="courses/{c['slug']}.html" style="--course:{c['color']}">
  <span class="code">{esc(c['code'])}</span>
  <span class="name"><strong>{esc(c['title'])}</strong>{ar}<em>{esc(c['audience'])}</em></span>
  <span class="count">{meta}</span>
</a></li>""")
        rows.append(f'<section class="group"><h3>{esc(g)}</h3><ul class="course-list">{"".join(items)}</ul></section>')

    body = f"""<main>
<section class="hero" id="about">
  <p class="eyebrow">Teaching material</p>
  <h1>{esc(I['name'])}</h1>
  <p class="role">{esc(I['title'])}</p>
  <p class="lede">{esc(I['research'])}</p>
  <p class="phd">{esc(I['phd'])}</p>
  <dl class="stats">
    <div><dt>Courses</dt><dd>{len(COURSES)}</dd></div>
    <div><dt>Lecture decks</dt><dd>{total_lec}</dd></div>
    <div><dt>Sheets, projects &amp; readings</dt><dd>{total_res}</dd></div>
  </dl>
</section>
<section id="courses" class="courses">
  <h2>Courses</h2>
  {''.join(rows)}
</section>
</main>"""
    return page(f"{I['name']} — Teaching", body)


def resource_list(items):
    li = []
    for title, kind, fid, tag in items:
        li.append(f"""<li><a href="{drive_url(kind, fid)}" target="_blank" rel="noopener">
<span class="tag tag-{tag}">{KIND_LABEL.get(tag, tag)}</span><span>{esc(title)}</span><span class="go" aria-hidden="true">↗</span></a></li>""")
    return f'<ul class="res">{"".join(li)}</ul>'


def course_page(i, c):
    prev_c = COURSES[i - 1]
    next_c = COURSES[(i + 1) % len(COURSES)]
    facts = [("Audience", c["audience"])]
    if c.get("prerequisite"):
        facts.append(("Prerequisite", c["prerequisite"]))
    if c.get("textbook"):
        facts.append(("Textbooks", c["textbook"]))
    facts_html = "".join(f"<div><dt>{k}</dt><dd>{esc(v)}</dd></div>" for k, v in facts)
    ar = f'<p class="ar big" lang="ar" dir="rtl">{esc(c["title_ar"])}</p>' if c.get("title_ar") else ""

    sections = []
    if c["lectures"]:
        rows = "".join(
            f"""<tr><td class="num">{n:02d}</td><td>{esc(t)}</td>
<td class="act"><a href="{drive_url('file', fid)}" target="_blank" rel="noopener">Slides <span aria-hidden="true">↗</span></a></td></tr>"""
            for n, (t, fid) in enumerate(c["lectures"], 1))
        sections.append(f"""<section><h2>Lectures</h2>
<div class="table-wrap"><table class="lectures"><thead><tr><th>No.</th><th>Topic</th><th><span class="sr">Open</span></th></tr></thead>
<tbody>{rows}</tbody></table></div></section>""")
    if c.get("resources"):
        sections.append(f"<section><h2>Problem sheets &amp; projects</h2>{resource_list(c['resources'])}</section>")
    for g, items in c.get("resource_groups", []):
        sections.append(f"<section><h2>{esc(g)}</h2>{resource_list(items)}</section>")
    if c.get("notes"):
        sections.append(f'<p class="note">{esc(c["notes"])}</p>')
    folder = (f'<a class="btn" href="{drive_url("folder", c["folder"])}" target="_blank" rel="noopener">Open course folder in Drive ↗</a>'
              if c.get("folder") else "")

    body = f"""<main class="course">
<p class="crumb"><a href="../index.html#courses">All courses</a></p>
<section class="course-head">
  <p class="code">{esc(c['code'])}</p>
  <h1>{esc(c['title'])}</h1>
  {ar}
  <p class="lede">{esc(c['summary'])}</p>
  <dl class="facts">{facts_html}</dl>
  {folder}
</section>
{''.join(sections)}
<nav class="pager" aria-label="Other courses">
  <a href="{prev_c['slug']}.html"><small>Previous course</small>{esc(prev_c['title'])}</a>
  <a href="{next_c['slug']}.html" class="next"><small>Next course</small>{esc(next_c['title'])}</a>
</nav>
</main>"""
    return page(f"{c['title']} — {I['name']}", body, depth=1, accent=c["color"])


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "courses").mkdir(parents=True)
    (OUT / "assets").mkdir()
    shutil.copy(ROOT / "src" / "style.css", OUT / "assets" / "style.css")
    (OUT / "index.html").write_text(index(), encoding="utf-8")
    for i, c in enumerate(COURSES):
        (OUT / "courses" / f"{c['slug']}.html").write_text(course_page(i, c), encoding="utf-8")
    print(f"Built {1 + len(COURSES)} pages into {OUT}")


if __name__ == "__main__":
    main()
