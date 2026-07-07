# WORKLOG

## 2026-06-25 22:50

项目立项。需求:Windows桌面喝水提醒小桌宠,UI简约、动效丝滑、非线性动画。

技术决策:
- 原计划 Tauri + Vue3,但本机未装 Rust 工具链,改用 Electron + Vue3(等价的前端动效能力,代价是包体积大)
- 桌宠形态:透明悬浮窗里一只水滴,呼吸式 idle 动画,到点触发"召唤序列"
- 不做数据记录,纯提醒(MVP)
- 提醒间隔固定可配(默认45分钟)

已完成:
- 工作区命名修正(water → 20260625-water-reminder)
- 项目 CLAUDE.md(技术栈/动效原则/视觉风格/禁用项)
- README(怎么跑/怎么打包)
- 本文件

## 2026-06-25 23:45

打包成 .exe 完成。

踩坑:
- electron 二进制默认走 GitHub releases,被网络卡了40+分钟。解决:项目级 `.npmrc` + 命令行 env 同时设 `ELECTRON_MIRROR` / `ELECTRON_BUILDER_BINARIES_MIRROR` 走淘宝镜像,11秒下完
- PIL 保存 ICO 时,主图传 16x16 会被 electron-builder 拒(要求 >= 256x256)。改成主图 256x256、sizes 列表第一个是 (256,256)
- 用 Python + Pillow + Cubic Bezier 画的水滴图标,产物 `build/icon.ico` / `build/icon.png`

产物:
- 安装包: `release/WaterReminder Setup 0.1.0.exe` (81MB)
- 免安装: `release/win-unpacked/WaterReminder.exe` (291MB 目录)


## 2026-06-29 17:22

新增功能:多杯型选择 + 历史记录。

数据模型扩展(electron-store):
- `cupPresets`:4 个杯型(小/中/大/水瓶,默认 150/250/350/500ml,可自定义)
- `dailyGoal`:每日目标,默认 2000ml
- `history`:按日期存条目 `{ 'YYYY-MM-DD': { total, entries: [{time, amount, cupId}] } }`

UI 改动:
- 桌宠窗口扩大 160x200 → 400x220,桌宠靠右,面板从左侧弹出(避免飞出屏幕)
- ActionPanel:头部进度环 + "今日 X/Y ml",中部 4 杯按钮(hover 杯内水位上升),底部稍后/设置链接
- 新增组件:ProgressRing(SVG 环 + GSAP 动画)、CupButton(杯型按钮)、BarChart(柱状图)
- Settings 加 tab:设置 / 今日 / 历史
  - 设置 tab:加每日目标输入 + 4 杯容量自定义
  - 今日 tab:大进度环(140px) + 三块统计(次数/完成度/还差) + 时间线
  - 历史 tab:7 日均值 + 达标天数 + 7 日柱状图(今日加亮 + 达标变绿 + 目标虚线)
- 桌宠"喝水"后 +XXXml 飞字动画(bounce.out → power2.in 上升淡出)

托盘菜单:
- 顶部展示 "今日 X / Y ml (Z%)"(disabled label)
- "现在就喝一杯" 改成 "我喝了" submenu,4 个杯型可选
- tray tooltip 也带今日累计

打包产物:`release/WaterReminder Setup 0.1.0.exe` (81MB)

## 2026-07-01 17:31

调整进化后的像素水龟形态。
改动:
- 重写 `scripts/generate-turtle.py`,从 48x48 改成 64x64 像素图,造型改为蓝色正面小水龟 + 厚背壳 + 双肩银灰水炮
- 重新生成 `src/assets/turtle.png` 和 `src/assets/turtle-preview.png`
- 放大 `Turtle.vue` 显示尺寸,让桌面小窗里的炮管、龟壳、腹甲更清楚

验证:
- `npm run build:vite` 通过

## 2026-07-01 17:44

新增小桌宠面板右上角"重置"。
改动:
- `ActionPanel.vue` 头部右侧新增重置按钮,保留 hover / active 动效
- `electron/main.cjs` 新增 `water:reset-today`,清空今天喝水记录并清掉当天进化标记,同时刷新托盘和设置页
- `electron/preload.cjs` 暴露 `water.resetToday()`
- `Pet.vue` 接入重置事件,点击后今日数据归零,进化形态切回水滴,显示"已重置"

验证:
- `node --check electron/main.cjs` 通过
- `node --check electron/preload.cjs` 通过
- `npm run build:vite` 通过

## 2026-07-01 17:54

用户反馈运行中小桌宠面板没显示"重置"。
确认:
- 源码和 `dist` 里已有重置按钮与 `water:reset-today`
- 截图来自旧安装版,不是最新构建

处理:
- 重新执行 `npm run build`,生成新的安装包 `release/WaterReminder Setup 0.1.0.exe`
- 新包已包含右上角重置按钮、今日数据重置、形态切回水滴逻辑

## 2026-07-07 15:24

准备上传 GitHub。
处理:
- 远端仓库 `ZD312RZJ/ZD312RZJ` 已有个人主页 `README.md`,为避免覆盖,项目放到仓库子目录 `20260625-water-reminder/`
- 上传内容为源码、脚本、文档、图标和项目说明,跳过 `node_modules`、`dist`、`release`
- 提交前执行密钥关键词扫描,未发现 token / secret / password / api key 等命中
- `npm run build:vite` 通过

## 2026-07-07 15:26

GitHub 上传完成。
结果:
- 已推送到 `https://github.com/zd312rzj/zd312rzj`
- 项目路径: `20260625-water-reminder/`
- 提交: `2bb4cd9 Add water reminder project`
- 保留仓库根目录原有个人主页 `README.md`,没有覆盖



## 2026-06-29 17:41

修面板和水滴隔太远 + 改触发方式。

改动:
- 触发从"hover 280ms 自动展开"改成"点击切换";鼠标移出整个 wrapper 时关闭
- 窗口缩到 380x220(原 400),消除中间空隙
- 面板紧贴水滴(side=right 时面板贴左 12px / 桌宠贴右 14px;side=left 时反过来)
- main 进程加 `computePetSide()`:根据桌宠中心相对屏幕中心判定 left/right,在 ready-to-show / moved / drag-end 时推送 'pet:side'
- ActionPanel 接 side prop:CSS 切左右贴合 + 入场动画方向跟着翻(从空白侧滑入)
- 拖到屏幕左半边自动翻转,面板从右侧弹出

重打:`release/WaterReminder Setup 0.1.0.exe`(81MB,覆盖安装,数据不丢)


## 2026-06-29 17:53

新增:达标进化彩蛋。

数据:
- electron-store 加 `lastEvolveDate`,记录最后一次进化日期
- `getToday()` 返回 `evolved` 字段(今日已达标且已记进化)

主进程:
- `recordDrink` 后判定 total >= goal 且 lastEvolveDate != today,首次达标 emit 'evolve'(每天只触发一次)

新组件:
- `Turtle.vue`:独立设计的卡通水龟(蓝身/绿龟壳/笑脸,通用萌宠元素,非任何已有 IP 的复刻)
- `EvolveOverlay.vue`:白光罩 + 光环 + 12 颗粒子飞散

动画(GSAP timeline,总时长约 3.1s):
- 0~0.9s:光环 scale 0.6→1.6 淡入,水滴抖动(7 次小幅 yoyo)
- 0.9~1.4s:白光罩 scale 0.3→1 淡入 + 水滴 scale 缩到 0,form 切到 turtle
- 1.45~2s:水龟 scale 0.4→1.15→1 back+elastic 出现
- 1.85~2.7s:burst 大光圈散开 + 12 颗粒子放射性飞出
- 2.7s 后白光罩淡出,气泡显示 "进化了"
- mounted 时如果 today.evolved=true,直接显示 turtle 不播动画

Pet.vue 重构:
- currentRef() 切 droplet/turtle 引用,呼吸/视差/抖动都跟随当前形态
- evolving 期间禁用点击/双击,避免动画被打断

打包产物:`release/WaterReminder Setup 0.1.0.exe` (81MB)
