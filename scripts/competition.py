#!/usr/bin/env python3
"""东南大学成贤学院 学科竞赛管理系统 (http://sy.cxxy.seu.edu.cn/js/) 自动化。

依赖：仅 Python 标准库。
账号密码一律由命令行/stdin 传入，不写死在脚本里。

用法：
  python competition.py login USER PWD        测试登录（只打印登录是否成功）
  python competition.py list USER PWD         列出可报名项目（自动翻页）
  python competition.py registered USER PWD   列出已报名项目
  python competition.py detail ITEMNO         项目详情（公开，无需登录；ITEMNO 为 32 位十六进制）
  python competition.py public-list           公开全部竞赛项目（无需登录）

密码位置填 "-" 表示从标准输入读取，避免密码留在命令行历史里。
"""
import sys
import re
import html
import urllib.request
import urllib.parse
import http.cookiejar

BASE = "http://sy.cxxy.seu.edu.cn/js/"


def build_opener():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op


def get(op, url, data=None):
    r = op.open(url, data=data, timeout=30)
    return r.read().decode("gbk", "ignore")


def field(name, text):
    m = re.search(r"name=['\"]" + re.escape(name) + r"['\"][^>]*value=['\"]([^'\"]*)", text)
    if not m:
        m = re.search(r"value=['\"]([^'\"]*)['\"][^>]*name=['\"]" + re.escape(name) + r"['\"]", text)
    return m.group(1) if m else ""


def form_fields(text):
    """把页面里的 <input> 和 <select> 收集成表单字典（忽略 submit/image）。"""
    d = {}
    for m in re.finditer(r"<input[^>]+>", text):
        tag = m.group(0)
        n = re.search(r'name=["\']([^"\']*)', tag)
        t = re.search(r'type=["\']([^"\']*)', tag)
        v = re.search(r'value=["\']([^"\']*)', tag)
        if not n:
            continue
        typ = (t.group(1) if t else "text").lower()
        if typ in ("submit", "image"):
            continue
        d[n.group(1)] = v.group(1) if v else ""
    for m in re.finditer(r'<select[^>]*name=["\']([^"\']*)["\'][^>]*>(.*?)</select>', text, re.S):
        sn = m.group(1)
        sh = m.group(2)
        s = re.search(r'<option[^>]*selected[^>]*value=["\']([^"\']*)', sh) or re.search(
            r'<option[^>]*value=["\']([^"\']*)', sh
        )
        d[sn] = s.group(1) if s else ""
    return d


def login(username, password):
    """登录竞赛系统，返回 (opener, sid, screen)。失败返回 (opener, None, None)。"""
    op = build_opener()
    pg = get(op, BASE + "index.aspx")
    data = urllib.parse.urlencode(
        {
            "__VIEWSTATE": field("__VIEWSTATE", pg),
            "__VIEWSTATEGENERATOR": field("__VIEWSTATEGENERATOR", pg),
            "__EVENTVALIDATION": field("__EVENTVALIDATION", pg),
            "UserId": username,
            "Pwd": password,
            "Append.x": "18",
            "Append.y": "18",
        }
    ).encode("ascii")
    t = get(op, BASE + "index.aspx", data)
    if "用户名或密码错误" in t:
        return op, None, None
    m = re.search(r"location\.href='([^']+)'", t)
    if not m:
        return op, None, None
    main_url = BASE + html.unescape(m.group(1))
    get(op, main_url)
    sid = re.search(r"sid=([^&]+)", main_url).group(1)
    screen = re.search(r"screen=([^&]+)", main_url).group(1)
    return op, sid, screen


def parse_item_rows(text):
    rows = []
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, re.S):
        r = m.group(1)
        if "itemlook.aspx" not in r:
            continue
        name_m = re.search(r"itemlook\.aspx[^>]*>(.*?)</a>", r, re.S)
        name = re.sub(r"<[^>]+>", "", name_m.group(1)).strip() if name_m else ""
        name = re.sub(r"\s+", " ", name)
        no_m = re.search(r"itemno=(\d+)", r)
        itemno = no_m.group(1) if no_m else ""
        date_m = re.search(r"报名日期</font></th>.*?</tr>", r, re.S)
        btn = re.search(r'name=["\']([^"\']*EditButton1[^"\']*)["\'][^>]*value=["\']进入["\']([^>]*)', r)
        enabled = None
        if btn:
            enabled = "disabled" not in btn.group(2)
        rows.append({"name": name, "itemno": itemno, "register_enabled": enabled})
    return rows


def list_competitions(op, sid, screen):
    """列出「项目列表」全部项目（含是否开放报名）。"""
    item_base = BASE + "Student/ItemList.aspx?sid=" + sid + "&screen=" + screen
    html_text = get(op, item_base)
    rows = parse_item_rows(html_text)
    for _ in range(2):  # 最多翻 2 页
        d = form_fields(html_text)
        d["__EVENTTARGET"] = "btnNext"
        d["__EVENTARGUMENT"] = ""
        try:
            html_text = get(op, item_base, urllib.parse.urlencode(d).encode("ascii"))
        except Exception:
            break
        rows += parse_item_rows(html_text)
    return rows


def registered(op, sid, screen):
    """列出「已报名项目」的文字摘要。"""
    url = BASE + "Student/MyitemList.aspx?sid=" + sid + "&screen=" + screen
    t = get(op, url)
    body = re.sub(r"<script.*?</script>", "", t, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"&nbsp;?", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return body


def detail(itemno):
    """公开项目详情（16 进制 ItemNo）。"""
    t = get(build_opener(), BASE + "ShowJingSaiXm.aspx?ItemNo=" + itemno)
    body = re.sub(r"<script.*?</script>", "", t, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"&nbsp;?", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return body


def public_list():
    """公开全部竞赛项目（标题 + ItemNo）。"""
    t = get(build_opener(), BASE + "MoreJingSaiXm.aspx")
    items = []
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']*ShowJingSaiXm[^"\']*)["\'][^>]*>(.*?)</a>', t, re.S):
        href = m.group(1)
        name = re.sub(r"<[^>]+>", "", m.group(2))
        name = re.sub(r"\s+", " ", name).strip()
        no = re.search(r"ItemNo=([0-9A-F]+)", href)
        items.append((name, no.group(1) if no else ""))
    return items


def _read_password(arg):
    if arg != "-":
        return arg
    return sys.stdin.readline().strip()


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == "public-list":
        for name, no in public_list():
            print(name, "\t", no)
        return 0
    if cmd == "detail":
        if len(argv) < 3:
            print("用法: competition.py detail ITEMNO")
            return 1
        print(detail(argv[2]))
        return 0
    if len(argv) < 4:
        print("用法: competition.py %s USER PWD" % cmd)
        return 1
    user, pwd = argv[2], _read_password(argv[3])
    op, sid, screen = login(user, pwd)
    if sid is None:
        print("登录失败：用户名或密码错误")
        return 1
    if cmd == "login":
        print("登录成功（不打印密码）")
    elif cmd == "list":
        for r in list_competitions(op, sid, screen):
            flag = "可报名" if r["register_enabled"] else ("-" if r["register_enabled"] is None else "已截止")
            print(f"{r['itemno']}\t{r['name']}\t{flag}")
    elif cmd == "registered":
        print(registered(op, sid, screen))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
