## 2026-07-08 14:50

调研抖音直播实时弹幕获取方案。结论：官方开放平台可通过直播小玩法互动数据接收评论推送，但不是任意直播间通用抓取；非官方 WebSocket 抓取技术上可行，核心是 room_id/live_id 解析、签名 WSS、心跳保活、gzip 解压和 protobuf 解析，生产使用风险较高。

## 2026-07-08 17:08

落地Node.js和TypeScript最小PoC。已实现CLI、直播间标识解析、签名服务适配、已签名WSS直连、WebSocket心跳、断线重连、gzip和protobuf解析、聊天弹幕JSON输出。签名算法未内置，改为通过已签名WSS或本地签名服务接入。

## 2026-07-08 17:19

新增`douyin_live_danmaku_test.py`单文件Python测试脚本。脚本支持输入房间号或直播间URL，默认请求本地`/sign`签名服务，也支持直接传已签名WSS；protobuf解析用脚本内置最小解析器，只额外依赖`websocket-client`。已做Python语法检查、帮助信息检查和签名服务不可用时的失败路径检查，并修正Windows中文输出编码。

## 2026-07-08 17:28

把Python脚本改成默认自动获取WSS：不传`--wss`和`--sign-url`时，用Playwright打开直播间页面，捕获`/webcast/im/push/v2/`连接和Cookie，再交给脚本监听弹幕。新增`requirements.txt`，README改成只输入房间号的运行方式。已验证Python语法、帮助信息和Chromium启动。

## 2026-07-08 17:34

用户运行后已成功捕获WSS并连接WebSocket，但解析首个数据包时报`unsupported protobuf wire type: 7`导致退出。已修改脚本：单个数据包解析失败不再终止监听，`--unknown`模式下会输出包长度和前16字节十六进制，方便继续判断协议或压缩格式问题。

## 2026-07-08 17:43

用户反馈持续输出`decode_error`。判断可能是WebSocket外层数据本身为gzip压缩，补充外层gzip自动解压后再解析PushFrame；同时限制非`--unknown`模式下只提示第一次解析失败，避免终端刷屏。已通过Python语法检查和帮助命令检查。

## 2026-07-08 17:51

用户反馈脚本只显示一次`decode_error`后像卡住。将默认模式改为浏览器直读：不再捕获WSS后用`websocket-client`二次连接，而是保持Playwright页面打开，监听页面内`/webcast/im/push/v2/`的`framereceived`事件并解析。新增15秒状态输出，显示收到帧数、解析错误数和弹幕数，避免空直播间或解析失败时无反馈。已通过Python语法检查和帮助命令检查。

## 2026-07-08 17:58

用户截图显示浏览器持续收到帧，`head_hex`为`080110...`，外层看起来是合法PushFrame，但全部解析失败。判断可能是内层payload为gzip但`payloadEncoding`字段未按预期解析，已改成只要payload以gzip魔数开头就解压；同时支持Playwright帧为base64字符串或Latin-1字符串的情况，并增强`--unknown`诊断输出，带上payload长度和payload头部十六进制。

## 2026-07-08 21:13

准备提交项目代码。补充`.gitignore`忽略Python缓存目录，避免把本地运行生成物提交进去。提交前已通过`python -m py_compile douyin_live_danmaku_test.py`和`npm run check`。

## 2026-07-08 21:46

实现本地Web弹幕看板，数据库改为MySQL。新增FastAPI服务、MySQL建库建表与查询层、浏览器弹幕采集控制、SSE实时推送、静态暗色看板页面和CSV导出。看板服务已启动在`http://127.0.0.1:8787`，已验证首页、状态接口、Python语法检查和旧Node类型检查；当前本机MySQL root空密码被拒绝，页面会显示明确的MySQL连接错误。

## 2026-07-08 22:01

按用户提供的本地MySQL连接信息重启看板服务，未把密码写入文件。已初始化`douyin_danmaku`库表，修复趋势统计SQL以兼容MySQL`only_full_group_by`模式，`/api/stats`已正常返回空统计。

## 2026-07-09 09:54

将MySQL连接信息保存到Windows用户环境变量，未写入项目文件；修改`run_dashboard.py`，双击时如果服务未启动会启动服务并自动打开看板，如果服务已启动则只打开页面。补充出库中文乱码修复，旧测试数据经API返回已恢复为正常Unicode。

## 2026-07-09 10:03

用户通过VS Code运行`run_dashboard.py`时使用了损坏的Python3.14环境，缺少`uvicorn`且标准库`socket/subprocess`也无法正常导入。新增`run_dashboard.cmd`，固定使用`D:\Anaconda3\python.exe`启动看板；`run_dashboard.py`在非Anaconda环境下给出明确提示。已验证`run_dashboard.cmd`能启动`127.0.0.1:8787`并返回当前会话状态。
## 2026-07-09 10:14

用户明确会在VS Code中选择`D:\Anaconda3\python.exe`，不需要额外`run_dashboard.cmd`启动器。已删除`run_dashboard.cmd`，重写`run_dashboard.py`和README，改为使用Anaconda解释器运行`run_dashboard.py`。已用Anaconda解释器完成语法检查，并验证`http://127.0.0.1:8787/api/session/current`正常返回。

## 2026-07-09 10:26

修复看板反复显示 MySQL 空密码错误的问题。原因是 8787 端口上还跑着旧的 `run_dashboard.py` 进程，旧进程启动时没有读到 MySQL 密码；已停止旧进程并重启服务。`run_dashboard.py` 现在会从 Windows 用户环境变量读取 MySQL 配置，发现旧服务仍是空密码错误时会自动停掉后重启。已用 `D:\Anaconda3\python.exe` 完成语法检查和 MySQL 初始化检查。

## 2026-07-17 15:39

将项目打包上传到 GitHub 仓库 `zd312rzj/zd312rzj`。远程仓库已有根目录 README 和 `20260625-water-reminder`，因此未覆盖根目录，而是把当前项目作为 `20260708-douyin-live-danmaku-research/` 子目录提交到 `main` 分支。上传前已确认 `.gitignore` 排除 `node_modules`、`dist`、缓存、`.env` 和日志，并完成 Python 语法检查、Node 类型检查与敏感词扫描。
