# 系统接口与登录流程备忘

以下为逆向得到的实际端点与关键细节，供脚本维护或现场排查用。账号密码**不要**写进任何文件。

## 1. 官网（公开）

- 学生事务列表：`/xsgg/list.htm`，翻页 `/xsgg/list2.htm` …（约 28 页）。
- 通知公告：`/xygg/list.htm`；教工事务：`/jsgg/list.htm`。
- 列表项链接形如 `/2026/0910/c379a62857/page.htm`。
- 学科竞赛目录(2024版) PDF 挂在 `eae.cxxy.seu.edu.cn` 的 `_upload/article/files/...` 下，见 `website.py catalog`。

## 2. 学科竞赛管理系统（sy.cxxy.seu.edu.cn/js，编码 GBK）

### 登录

1. `GET index.aspx`，取 `__VIEWSTATE`、`__VIEWSTATEGENERATOR`、`__EVENTVALIDATION`。
2. `POST index.aspx`：上述三字段 + `UserId` + `Pwd` + `Append.x=18` + `Append.y=18`。
3. 成功响应含 `location.href='Main/Main.aspx?sid=...&screen=...'`；失败含 `用户名或密码错误`。
4. 打开 `Main.aspx?sid=...&screen=...` 后，`sid`/`screen` 需在后续 URL 中一直带上。

### 学生侧页面

- 项目列表（可报名）：`Student/ItemList.aspx?sid=..&screen=..`
  - 表格每行有「进入」按钮 `gridview$ctlNN$EditButton1`；有 `disabled` 属性 = 报名已截止/未开放。
  - 翻页用 `__doPostBack('btnNext','')`：把页面表单字段 + `__EVENTTARGET=btnNext` POST 回去。
  - 搜索：表单字段 `txtItemCode`(项目编号)、`txtItemName`(项目名称)、`ddlJBFB`(立项等级)，提交按钮 `Append=查询`。
- 已报名项目：`Student/MyitemList.aspx?sid=..&screen=..`
  - 含「申报人 + 团队组员(学号)」，可用来核对队友学号。
- 修改密码：`Admin/MiMa.aspx?sid=..&screen=..`。

### 公开页面（无需登录）

- 项目详情：`ShowJingSaiXm.aspx?ItemNo=<32位十六进制>`，含负责人/等级/人数/时间/参赛学院年级/报名方式。
- 全部项目列表：`MoreJingSaiXm.aspx`（约 900+ 条，含历史）。

### 报名流程

1. `ItemList.aspx` 找到目标比赛，点「进入」（POST 对应按钮名）。
2. 后续是团队组建页：填作品名称、加队员（按学号）。
3. 报名为外部写入：提交前务必把「比赛/队长/队员/作品名」与用户确认。

## 3. 数字校园门户（my.cxxy.seu.edu.cn，编码 UTF-8）

### 登录

1. `GET /` 取会话。
2. `POST /userPasswordValidate.portal`：`Login.Token1=用户名` + `Login.Token2=密码`。
3. 成功响应含 `(opener||parent).handleLoginSuccessed()`，并下发 `iPlanetDirectoryPro` 会话 Cookie（Domain `.cxxy.seu.edu.cn`）。

### 页面

- 首页：`index.portal`；「我的学习」`index.portal?.pn=p43`；「个人信息」`index.portal?.pn=p44`。
- 门户本身只有服务入口，成绩/课表在教务系统里。

## 4. 教务系统（经门户 SSO）

- 旧系统 jw2（金智 epstar，IE-only）：`http://jw2.cxxy.seu.edu.cn/epstar/web/swms/mainframe/homePage.jsp`
  - 带 `iPlanetDirectoryPro` Cookie 即可进入；数据走 `template.jsp?mainobj=...&tfile=...`，菜单由数据库动态生成，需现场抓包定位成绩/课表接口。
- 新系统 jwfw（师生服务端，现代浏览器可开）：`http://jwfw.cxxy.seu.edu.cn/ssfw/`
  - SSO 入口 `/ssfw/j_spring_ids_security_check`，成功后 `welcome/index.do`。
  - 学生菜单由 AJAX 加载；成绩/课表需现场从菜单定位具体 `.do` 接口。

## 排查提示

- 竞赛系统编码是 GBK，门户/教务是 UTF-8，解码别用错。
- 各系统都需要 `User-Agent`，教务系统需要 `Referer`。
- 登录失败先核对：竞赛系统用「学号(8位)」，门户用「校园卡号(9位)」，两者账号不同。
