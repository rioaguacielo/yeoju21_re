#!/usr/bin/env python3
"""여주시 지속가능발전협의회 사이트 생성기.

content/<게시판>/*.md 글 파일과 templates/ 를 읽어 _site/ 에 완성된 HTML을 만듭니다.
GitHub Actions(.github/workflows/deploy.yml)가 글이 올라올 때마다 자동으로 실행합니다.

로컬 실행:  python3 scripts/build.py   (필요 패키지: pyyaml, jinja2, markdown)
"""
import datetime as dt
import os
import re
import shutil
import sys
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
KST = dt.timezone(dt.timedelta(hours=9))
STATIC_DIRS = ["css", "images", "uploads"]


def load_site():
    site = yaml.safe_load((ROOT / "site.yml").read_text(encoding="utf-8"))
    base = os.environ.get("BASEURL", site.get("baseurl", "")) or ""
    return site, base.rstrip("/")


def parse_date(v):
    if isinstance(v, dt.datetime):
        d = v
    elif isinstance(v, dt.date):
        d = dt.datetime(v.year, v.month, v.day)
    elif isinstance(v, str) and v.strip():
        s = v.strip().replace(".", "-").replace("T", " ")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                d = dt.datetime.strptime(s[:19], fmt)
                break
            except ValueError:
                continue
        else:
            d = dt.datetime(1970, 1, 1)
    else:
        d = dt.datetime(1970, 1, 1)
    return d.replace(tzinfo=None)


def read_md(path: Path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        body = m.group(2)
    return meta, body


def human_size(n):
    if n >= 1024 * 1024:
        return f"{n / 1024 / 1024:.1f}MB"
    return f"{max(1, round(n / 1024))}KB"


def youtube_id(v):
    if not v:
        return None
    m = re.search(r"(?:youtu\.be/|v=|embed/|shorts/)([A-Za-z0-9_-]{6,})", str(v))
    return m.group(1) if m else None


def fix_urls(html, base):
    # CMS가 넣는 /uploads/... 경로에 사이트 하위 경로를 붙입니다.
    if not base:
        return html
    # 사이트 안 링크(/uploads/..., /notice/... 등)에 하위 경로를 붙입니다.
    return re.sub(r'(src|href)=(["\'])/(?!/)(?!' + re.escape(base.lstrip("/")) + r'/)', rf'\1=\2{base}/', html)


def load_posts(site, base):
    posts_by_board = {}
    for key, cfg in site["boards"].items():
        folder = ROOT / "content" / key
        posts = []
        for f in sorted(folder.glob("*.md")) if folder.exists() else []:
            meta, body = read_md(f)
            if meta.get("draft"):
                continue
            body = body.strip()
            if body.startswith("<"):
                html = body
            else:
                html = markdown.markdown(body, extensions=["extra", "nl2br", "sane_lists"])
            html = fix_urls(html, base)
            date = parse_date(meta.get("date"))
            atts = []
            for a in meta.get("attachments") or []:
                if isinstance(a, dict):
                    path, name = a.get("file") or a.get("path"), a.get("name")
                else:
                    path, name = str(a), None
                if not path:
                    continue
                local = ROOT / path.lstrip("/")
                size = human_size(local.stat().st_size) if local.exists() else None
                url = base + path if path.startswith("/") else path
                atts.append({"name": name or Path(path).name, "url": url, "size": size})
            thumb = meta.get("thumbnail")
            if thumb:
                thumb = base + thumb if str(thumb).startswith("/") else thumb
            else:
                m = re.search(r'<img[^>]+src=["\']([^"\']+)', html)
                thumb = m.group(1) if m else None
            yt = youtube_id(meta.get("youtube"))
            if not thumb and yt:
                thumb = f"https://img.youtube.com/vi/{yt}/hqdefault.jpg"
            if not thumb:
                m = re.search(r'youtube\.com/embed/([A-Za-z0-9_-]+)', html)
                if m:
                    thumb = f"https://img.youtube.com/vi/{m.group(1)}/hqdefault.jpg"
            slug = f.stem
            posts.append({
                "slug": slug,
                "board": key,
                "title": str(meta.get("title") or slug),
                "author": meta.get("author") or site["title"],
                "date": date,
                "date_str": date.strftime("%Y.%m.%d"),
                "date_str_full": date.strftime("%Y.%m.%d %H:%M"),
                "html": html,
                "attachments": atts,
                "thumb": thumb,
                "youtube_id": yt,
                "url": f"{base}/{key}/{slug}/",
            })
        posts.sort(key=lambda p: p["date"], reverse=True)
        posts_by_board[key] = posts
    return posts_by_board


def main():
    site, base = load_site()
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]))
    build_id = dt.datetime.now(KST).strftime("%Y%m%d%H%M")
    boards = {k: {"key": k, **v} for k, v in site["boards"].items()}
    group_of = {b: g for g, gc in site["groups"].items() for b in gc["boards"]}
    posts = load_posts(site, base)
    common = {"site": site, "base": base, "build_id": build_id, "boards": boards, "posts": posts}

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for d in STATIC_DIRS:
        if (ROOT / d).exists():
            shutil.copytree(ROOT / d, OUT / d)
    (OUT / ".nojekyll").write_text("")

    def write(rel, html):
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")

    # 고정 페이지
    page_out = {"home": "index.html", "about": "about.html", "sdgs": "sdgs.html", "action": "action.html", "rule": "rule.html", "404": "404.html"}
    for name, out in page_out.items():
        tpl = ROOT / "templates" / "pages" / f"{name}.html"
        if tpl.exists():
            write(out, env.get_template(f"pages/{name}.html").render(**common))

    # 게시판
    count = 0
    for key, board in boards.items():
        g = group_of.get(key)
        group = {"key": g, **site["groups"][g]} if g else {"label": board["label"]}
        group_boards = [boards[b] for b in site["groups"][g]["boards"]] if g else [board]
        lst = posts[key]
        ctx = dict(common, board=board, group=group, group_boards=group_boards, nav=g if g in ("community", "gallery") else "action")
        write(f"{key}/index.html", env.get_template("board.html").render(items=lst, **ctx))
        for i, p in enumerate(lst):
            older = lst[i + 1] if i + 1 < len(lst) else None
            newer = lst[i - 1] if i > 0 else None
            write(f"{key}/{p['slug']}/index.html", env.get_template("post.html").render(post=p, prev=older, next=newer, **ctx))
            count += 1
    print(f"built {count} posts in {len(boards)} boards -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
