# CLAUDE.md — 喝水提醒小桌宠

## 项目定位

Windows桌面常驻的喝水提醒小工具。形态是一个透明悬浮窗里的小桌宠(水滴形象),平时呼吸式动画,到点会"动起来"吸引注意。强调亲提醒感、UI简约、动效丝滑且非线性。

## 技术栈

- Electron 35+（主进程,负责托盘/窗口/定时器/系统通知）
- Vue 3.5 + Vite 6（渲染进程,组件 + 状态）
- Tailwind CSS 4（样式)
- GSAP 3（动效引擎,非线性动画首选,比CSS keyframe表现力强）
- electron-store（配置持久化）
- electron-builder（打包成 .exe）

## 目录结构

```
20260625-water-reminder/
├── CLAUDE.md            # 本文件
├── README.md            # 给人看的说明
├── WORKLOG.md           # 工作日志
├── docs/                # AC、设计方案
├── electron/            # 主进程代码
│   ├── main.js          # 入口、窗口、托盘、定时器
│   ├── preload.js       # IPC 桥
│   └── store.js         # 配置持久化
├── src/                 # 渲染进程(Vue)
│   ├── App.vue          # 根组件
│   ├── components/      # Pet / Panel / Settings
│   ├── composables/     # useReminder / useAnimation
│   ├── assets/          # SVG/图片
│   └── main.js
├── index.html
├── vite.config.js
└── package.json
```

## 动效原则（项目核心,不可妥协）

1. **禁止使用 linear 缓动**。所有过渡至少用 `cubic-bezier(0.34, 1.56, 0.64, 1)` 这类非线性曲线,或 GSAP 的 `power2.inOut` / `back.out` / `elastic.out`。
2. **每个交互至少有3层状态**:idle / hover / active,且状态间用动画过渡,不允许瞬间切换。
3. **提醒触发的"召唤序列"是产品灵魂**: 至少包含 缩放预备 → 弹跳 → 颜色变化 → 文字fade-in 四个阶段,用 GSAP timeline 编排,总时长 800ms~1200ms。
4. **呼吸动画**: idle 状态下桌宠用 4 秒一个循环的 scale(1 → 1.04 → 1) + opacity(0.85 → 1 → 0.85),sine 缓动。
5. **入场和出场分别设计**: 入场略慢(出现感),出场略快(干脆利落),时长比 1.5:1 起步。
6. **尊重 `prefers-reduced-motion`**: 系统层开启减少动画时,降级为简单 fade。
7. **避免任何"原生 Web 弹窗感"**: 不用 alert/confirm,所有交互在自研组件里完成。

## 视觉风格

- 主色调: 海蓝(#4FB7E0)到青绿(#5FD9CB)的渐变,代表水
- 背景: 深空灰(#1A1D24)半透明 + backdrop-filter blur,玻璃拟态
- 字体: PingFang SC / Microsoft YaHei UI,数字用等宽
- 圆角: 桌宠主体 50%(圆形),面板 16px,按钮 12px
- 阴影: 桌宠带柔光晕(box-shadow + filter:drop-shadow 双重)

## 禁用项

- **禁止用 emoji**,除非用户明确要求
- **禁止 AI 腔表达**(全局 no_ai_style 规则)
- **不写超过单行的注释**,代码靠命名表达
- **不加未来扩展的抽象**: 这是个人小工具,不为假想需求做架构
- **不写文档之外的 README/解释性 md**(除非用户要)
- **windows 上 curl 中文 JSON 必出乱码**(若涉及外部 API,用 Python 或 Node 调,不走 curl)

## 启动命令

```bash
npm install
npm run dev          # 开发模式(electron + vite hmr)
npm run build        # 打包成 win 安装包
```

## 配置持久化

用 electron-store,默认配置:

```js
{
  intervalMinutes: 45,
  startOnBoot: false,
  soundEnabled: true,
  petPosition: { x: null, y: null }  // null = 右下默认位置
}
```

## 数据模型(electron-store 实际 schema)

```js
{
  intervalMinutes: 45,
  startOnBoot: false,
  soundEnabled: true,
  petPosition: { x: null, y: null },
  cupPresets: [
    { id: 'small',  label: '小杯', amount: 150 },
    { id: 'medium', label: '中杯', amount: 250 },
    { id: 'large',  label: '大杯', amount: 350 },
    { id: 'bottle', label: '水瓶', amount: 500 }
  ],
  dailyGoal: 2000,                      // ml
  history: {
    'YYYY-MM-DD': {
      total: number,                     // 当日累计 ml
      entries: [{ time: ms, amount: ml, cupId: string }]
    }
  }
}
```

## 后续可能的扩展(不做,留记号)

- 30 日 / 月历视图(当前只看 7 日)
- 喝水提醒声音可选多种
- 多种桌宠形象切换
- 自定义提醒文案
- 移动到 Tauri(包体优化,前端代码可直接复用)
