#!/usr/bin/env python3
"""东南大学成贤学院官网 (http://cxxy.seu.edu.cn/) 公开信息抓取。

无需登录。依赖：仅 Python 标准库。

用法：
  python website.py notices [栏目]   栏目默认 xsgg(学生事务)，可填 xygg(通知公告)/jsgg(教工事务)
  python website.py search 关键词     在学生事务/通知公告/教工事务里搜关键词
  python website.py catalog          学科竞赛目录(2024版) 摘要
"""
import sys
import re
import urllib.request

BASE = "http://cxxy.seu.edu.cn/"
COLUMNS = {"xsgg": "学生事务", "xygg": "通知公告", "jsgg": "教工事务"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def _parse_list(html_text):
    out = []
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html_text, re.S):
        href = m.group(1)
        text = re.sub(r"<[^>]+>", "", m.group(2))
        text = re.sub(r"\s+", " ", text).strip()
        if text and "page.htm" in href:
            out.append((text, href))
    return out


def notices(column="xsgg", pages=28):
    col = column if column in COLUMNS else "xsgg"
    items = []
    for i in range(1, pages + 1):
        path = f"/{col}/list.htm" if i == 1 else f"/{col}/list{i}.htm"
        try:
            html_text = get(BASE + path)
        except Exception:
            break
        items += _parse_list(html_text)
    return items


def search(keyword, pages=28):
    hits = []
    for col in COLUMNS:
        for text, href in notices(col, pages):
            if keyword in text:
                hits.append((COLUMNS[col], text, href))
    return hits


def catalog():
    """返回学科竞赛目录(2024版) PDF 的 URL 与说明。"""
    # 目录 PDF 挂在电工电子实验中心网站；这里给出已知入口，正文需用 pdftotext 解析。
    url = "http://eae.cxxy.seu.edu.cn/_upload/article/files/03/8a/b5a48a1143448abb6cde8f18e738/a9749cf3-0fbd-49a0-8440-d19f16d390bb.pdf"
    return [
        ("学科竞赛目录(2024版)", url),
        ("说明", "下载后用 pdftotext -layout 提取正文，含 A/B/C 类与承办学院。"),
    ]


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == "notices":
        col = argv[2] if len(argv) > 2 else "xsgg"
        for text, href in notices(col):
            print(text, "->", BASE + href.lstrip("/"))
    elif cmd == "search":
        if len(argv) < 3:
            print("用法: website.py search 关键词")
            return 1
        for col, text, href in search(argv[2]):
            print(f"[{col}] {text} -> {BASE}{href.lstrip('/')}")
    elif cmd == "catalog":
        for k, v in catalog():
            print(k, ":", v)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
