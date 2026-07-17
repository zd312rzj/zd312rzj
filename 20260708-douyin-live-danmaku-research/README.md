# Douyin Live Danmaku Dashboard

## 做什么

这是一个本地抖音直播弹幕看板。它会打开浏览器监听直播间WebSocket，解析实时弹幕，写入MySQL，并在本地Web页面展示弹幕、基础指标、趋势、关键词和用户发言榜。

适合本地技术验证、自有直播间观察和运营复盘。不内置抖音签名算法，不保存账号密码、token或固定Cookie。

## 运行看板

安装依赖，装过就不用重复：

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

本机MySQL连接信息已保存到Windows用户环境变量。启动前在VS Code里选择Python解释器：

```text
D:\Anaconda3\python.exe
```

然后运行：

```bash
python run_dashboard.py
```

脚本会启动本地服务，并自动打开：

```text
http://127.0.0.1:8787
```

如果服务已经在运行，再次运行`run_dashboard.py`只会打开看板页面，不会重复启动服务。

命令行也可以直接运行：

```bash
D:\Anaconda3\python.exe run_dashboard.py
```

在页面输入直播间房间号或URL，点击开始。

## MySQL

默认读取这些环境变量：

```text
DANMAKU_DB_HOST
DANMAKU_DB_PORT
DANMAKU_DB_USER
DANMAKU_DB_PASSWORD
DANMAKU_DB_NAME
```

当前本机已配置为：

```text
host: 127.0.0.1
port: 3306
user: root
database: douyin_danmaku
```

密码保存在Windows用户环境变量，不写入项目文件。

## API

- `POST /api/session/start`：启动监听，参数`room`和`headless`
- `POST /api/session/stop`：停止监听
- `GET /api/session/current`：当前连接状态
- `GET /api/messages?limit=200`：最近弹幕
- `GET /api/stats`：总量、近1分钟、活跃用户、关键词和趋势
- `GET /api/ranking/users`：用户发言榜
- `GET /api/export/messages.csv`：导出弹幕CSV
- `GET /api/events`：SSE实时事件流

## 单文件测试脚本

保留原来的命令行测试脚本：

```bash
python douyin_live_danmaku_test.py
```

或直接传房间号：

```bash
python douyin_live_danmaku_test.py 123456
```

看到`type=chat`的JSON输出，说明弹幕获取正常。

## 目录说明

- `dashboard_app/`：FastAPI后端、MySQL数据库层、采集控制和静态看板
- `dashboard_app/static/`：看板HTML、CSS和JS
- `douyin_live_danmaku_test.py`：单文件弹幕测试脚本
- `run_dashboard.py`：本地看板Python服务入口
- `src/`：早期Node.js PoC代码，保留作参考
- `WORKLOG.md`：工作记录

## 限制

- 第一版只解析弹幕，不解析礼物、点赞、进场和粉丝团
- MySQL账号需要能创建数据库和表；如果没有权限，请先手动创建`DANMAKU_DB_NAME`对应数据库
- 抖音页面若出现验证码、登录页或地区限制，采集会停止并在看板显示错误
- 平台协议变化时，需要更新弹幕解析逻辑
