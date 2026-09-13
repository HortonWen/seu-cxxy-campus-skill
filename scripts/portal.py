#!/usr/bin/env python3
"""东南大学成贤学院 数字校园门户 (http://my.cxxy.seu.edu.cn/) 自动化。

依赖：仅 Python 标准库。
账号密码一律由命令行/stdin 传入，不写死。

用法：
  python portal.py login USER PWD      测试登录，打印门户身份（姓名/身份/校园卡号）
  python portal.py profile USER PWD    门户首页身份摘要
  python portal.py sso-jw USER PWD     经单点登录访问旧教务系统(jw2)主页，打印菜单/标题
  python portal.py sso-jwfw USER PWD   经单点登录访问新师生服务端(jwfw)，打印欢迎页

密码位置填 "-" 表示从标准输入读取。
"""
import sys
import re
import html
import urllib.request
import urllib.parse
import http.cookiejar

PORTAL = "http://my.cxxy.seu.edu.cn/"


def build_opener():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op


def get(op, url, data=None, referer=None):
    headers = {}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, data=data, headers=headers)
    r = op.open(req, timeout=30)
    return r.read().decode("utf-8", "ignore")


def login(username, password):
    """登录门户，成功返回 opener（含 iPlanetDirectoryPro 会话），失败返回 None。"""
    op = build_opener()
    get(op, PORTAL, referer=PORTAL)
    data = urllib.parse.urlencode(
        {"Login.Token1": username, "Login.Token2": password}
    ).encode("utf-8")
    t = get(op, PORTAL + "userPasswordValidate.portal", data=data, referer=PORTAL)
    if "handleLoginSuccessed" not in t:
        return None
    return op


def totext(html_text):
    b = re.sub(r"<script.*?</script>", "", html_text, flags=re.S)
    b = re.sub(r"<style.*?</style>", "", b, flags=re.S)
    b = re.sub(r"<[^>]+>", " ", b)
    b = re.sub(r"&nbsp;?", " ", b)
    b = re.sub(r"\s+", " ", b).strip()
    return b


def profile(op):
    t = get(op, PORTAL + "index.portal", referer=PORTAL)
    return totext(t)


def sso_jw(op):
    """经门户 SSO 访问旧教务系统 jw2，返回主页文本（含菜单项）。"""
    t = get(op, "http://jw2.cxxy.seu.edu.cn/epstar/web/swms/mainframe/homePage.jsp", referer=PORTAL)
    return totext(t)


def sso_jwfw(op):
    """经门户 SSO 访问新师生服务端 jwfw，返回欢迎页文本。"""
    get(op, "http://jwfw.cxxy.seu.edu.cn/ssfw/j_spring_ids_security_check", referer=PORTAL)
    t = get(op, "http://jwfw.cxxy.seu.edu.cn/ssfw/welcome/index.do", referer=PORTAL)
    return totext(t)


def _read_password(arg):
    if arg != "-":
        return arg
    return sys.stdin.readline().strip()


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 1
    cmd = argv[1]
    user, pwd = argv[2], _read_password(argv[3])
    op = login(user, pwd)
    if op is None:
        print("门户登录失败：用户名或密码错误")
        return 1
    if cmd == "login" or cmd == "profile":
        print(profile(op))
    elif cmd == "sso-jw":
        print(sso_jw(op))
    elif cmd == "sso-jwfw":
        print(sso_jwfw(op))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
