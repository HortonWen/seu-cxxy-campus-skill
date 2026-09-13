---
name: cxxy-campus
description: Automate 东南大学成贤学院 (CXXY) campus systems with the user's own credentials — crawl the official website, list/query/register competitions in the 学科竞赛管理系统, and sign in to the 数字校园门户 to reach the 教务系统.
---

# 东南大学成贤学院校园系统自动化

用账号密码替用户操作东南大学成贤学院的几个校内系统：官网、学科竞赛管理系统、数字校园门户（含单点登录进教务系统）。

## 适用场景

- 用户要查官网通知/学科竞赛目录、某个比赛是否开放报名。
- 用户要给竞赛管理系统里的比赛报名（本人队长 + 队友）。
- 用户要登录数字门户、进而查询课表/成绩等信息。

## 系统与登录入口

| 系统 | 地址 | 说明 |
|---|---|---|
| 官网 | http://cxxy.seu.edu.cn/ | 公开，无需登录 |
| 学科竞赛管理系统 | http://sy.cxxy.seu.edu.cn/js/ | 用户名=学号，密码=登录密码 |
| 数字校园门户 | http://my.cxxy.seu.edu.cn/ | 用户名=校园卡号(9位)，密码=门户密码 |
| 教务系统(旧) | http://jw2.cxxy.seu.edu.cn/ | 经门户 SSO，IE-only，脚本可绕开浏览器 |
| 教务系统(新·师生服务端) | http://jwfw.cxxy.seu.edu.cn/ssfw/ | 经门户 SSO，现代浏览器可开 |

详细接口与登录流程见 `references/endpoints.md`。

## 脚本

所有脚本只用 Python 标准库（`urllib` + `http.cookiejar`），无需安装第三方包。

```bash
# 官网（公开，无需登录）
python scripts/website.py notices               # 学生事务/通知公告列表
python scripts/website.py search 关键词          # 按关键词搜官网通知
python scripts/website.py catalog               # 学科竞赛目录(2024版)摘要

# 学科竞赛系统
python scripts/competition.py login USER PWD     # 测试登录
python scripts/competition.py list USER PWD      # 列出可报名项目（全部页）
python scripts/competition.py registered USER PWD # 已报名项目
python scripts/competition.py detail ITEMNO      # 项目详情（公开）
python scripts/competition.py public-list        # 公开全部竞赛项目（无需登录）

# 数字门户
python scripts/portal.py login USER PWD          # 测试门户登录 + 打印身份
python scripts/portal.py profile USER PWD        # 门户首页身份信息
python scripts/portal.py sso-jw USER PWD         # 单点登录到教务系统(旧)
python scripts/portal.py sso-jwfw USER PWD       # 单点登录到师生服务端(新)
```

密码可以用 `-` 代替，脚本会从标准输入读取（避免密码留在命令行历史里）。

## 安全约定（必须遵守）

- 账号密码只来自用户本次提供的输入，**绝不写进脚本、配置文件或日志**。
- 只操作用户本人的账号；不为其他人报名。
- 报名是真实外部写入操作：**提交前把「比赛名称 + 队长 + 队员学号/姓名 + 作品名称」念给用户确认**，确认后再提交。
- 不要用这些账号尝试越权、批量注册或任何与用户请求无关的动作。

## 报名流程要点

竞赛系统的报名是「队长建队」模式：

1. 登录后打开 `Student/ItemList.aspx`（项目列表），每个项目的「进入」按钮是报名入口；只有按钮未 `disabled` 的项目才开放报名。
2. 点「进入」跳到团队组建页，需填作品名称并把队员（按学号）加进队伍。
3. 报名截止日期写在各项目详情和「报名日期」列里；若目标比赛不在列表里，说明系统尚未开放该比赛线上报名，应提示用户联系竞赛负责人或加通知里的 QQ 群，不要凭空代报。

接口、字段名和抓取细节见 `references/endpoints.md`。
