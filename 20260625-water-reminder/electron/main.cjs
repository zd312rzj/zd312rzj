const { app, BrowserWindow, Tray, Menu, Notification, screen, ipcMain, nativeImage, shell } = require('electron')
const path = require('node:path')
const AutoLaunch = require('auto-launch')

const isDev = process.env.NODE_ENV === 'development'
const DEV_URL = 'http://localhost:5173'

let petWindow = null
let settingsWindow = null
let tray = null
let reminderTimer = null
let store = null

const PET_SIZE = { width: 380, height: 220 }
const SETTINGS_SIZE = { width: 480, height: 560 }

function computePetSide() {
  if (!petWindow) return 'right'
  const [winX] = petWindow.getPosition()
  const centerX = winX + PET_SIZE.width / 2
  const display = screen.getDisplayNearestPoint({ x: centerX, y: 0 })
  const screenCenterX = display.workArea.x + display.workArea.width / 2
  return centerX >= screenCenterX ? 'right' : 'left'
}

function emitPetSide() {
  if (!petWindow || petWindow.isDestroyed()) return
  petWindow.webContents.send('pet:side', computePetSide())
}

const autoLauncher = new AutoLaunch({ name: 'WaterReminder', isHidden: true })

const singleLock = app.requestSingleInstanceLock()
if (!singleLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (petWindow) {
      petWindow.show()
      petWindow.focus()
    }
  })
}

async function initStore() {
  const { default: Store } = await import('electron-store')
  store = new Store({
    defaults: {
      intervalMinutes: 45,
      startOnBoot: false,
      soundEnabled: true,
      petPosition: { x: null, y: null },
      cupPresets: [
        { id: 'small', label: '小杯', amount: 150 },
        { id: 'medium', label: '中杯', amount: 250 },
        { id: 'large', label: '大杯', amount: 350 },
        { id: 'bottle', label: '水瓶', amount: 500 }
      ],
      dailyGoal: 2000,
      history: {},
      lastEvolveDate: null
    }
  })
}

function todayKey() {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function logWater(amount, cupId) {
  const history = store.get('history') || {}
  const key = todayKey()
  const day = history[key] || { total: 0, entries: [] }
  day.entries.push({ time: Date.now(), amount, cupId })
  day.total = day.entries.reduce((s, e) => s + e.amount, 0)
  history[key] = day
  store.set('history', history)
  return day
}

function getToday() {
  const history = store.get('history') || {}
  const goal = store.get('dailyGoal')
  const day = history[todayKey()] || { total: 0, entries: [] }
  const evolved = store.get('lastEvolveDate') === todayKey() && day.total >= goal
  return {
    ...day,
    goal,
    progress: goal > 0 ? Math.min(1, day.total / goal) : 0,
    evolved
  }
}

function resetTodayWater() {
  const history = store.get('history') || {}
  const key = todayKey()
  history[key] = { total: 0, entries: [] }
  store.set('history', history)
  if (store.get('lastEvolveDate') === key) store.set('lastEvolveDate', null)
  return getToday()
}

function getHistory(days = 7) {
  const history = store.get('history') || {}
  const goal = store.get('dailyGoal')
  const result = []
  const now = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const key = `${y}-${m}-${day}`
    const rec = history[key] || { total: 0, entries: [] }
    result.push({
      date: key,
      label: `${d.getMonth() + 1}/${d.getDate()}`,
      total: rec.total,
      goal,
      isToday: i === 0
    })
  }
  return { days: result, goal }
}

function getDefaultPetPosition() {
  const { workArea } = screen.getPrimaryDisplay()
  return {
    x: workArea.x + workArea.width - PET_SIZE.width - 40,
    y: workArea.y + workArea.height - PET_SIZE.height - 40
  }
}

function createPetWindow() {
  const saved = store.get('petPosition')
  const pos = (saved.x != null && saved.y != null) ? saved : getDefaultPetPosition()

  petWindow = new BrowserWindow({
    width: PET_SIZE.width,
    height: PET_SIZE.height,
    x: pos.x,
    y: pos.y,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: true,
    hasShadow: false,
    focusable: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  petWindow.setAlwaysOnTop(true, 'screen-saver')
  petWindow.setVisibleOnAllWorkspaces(true)

  const url = isDev ? DEV_URL : `file://${path.join(__dirname, '..', 'dist', 'index.html')}`
  petWindow.loadURL(url)

  petWindow.once('ready-to-show', () => {
    petWindow.show()
    emitPetSide()
  })

  petWindow.webContents.on('did-finish-load', () => emitPetSide())

  petWindow.on('moved', () => {
    const [x, y] = petWindow.getPosition()
    store.set('petPosition', { x, y })
    emitPetSide()
  })

  petWindow.on('closed', () => { petWindow = null })
}

function createSettingsWindow() {
  if (settingsWindow) {
    settingsWindow.show()
    settingsWindow.focus()
    return
  }

  settingsWindow = new BrowserWindow({
    width: SETTINGS_SIZE.width,
    height: SETTINGS_SIZE.height,
    frame: false,
    transparent: true,
    resizable: false,
    skipTaskbar: false,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  const url = isDev
    ? `${DEV_URL}/settings.html`
    : `file://${path.join(__dirname, '..', 'dist', 'settings.html')}`
  settingsWindow.loadURL(url)

  settingsWindow.once('ready-to-show', () => settingsWindow.show())
  settingsWindow.on('closed', () => { settingsWindow = null })
}

function buildTrayIcon() {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
    <defs>
      <linearGradient id="g" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="#4FB7E0"/>
        <stop offset="100%" stop-color="#5FD9CB"/>
      </linearGradient>
    </defs>
    <path d="M16 4 C 22 12 26 18 26 22 a10 10 0 0 1 -20 0 C 6 18 10 12 16 4 Z" fill="url(#g)"/>
  </svg>`
  return nativeImage.createFromBuffer(Buffer.from(svg))
}

function createTray() {
  tray = new Tray(buildTrayIcon())
  tray.setToolTip('喝水提醒')

  refreshTrayMenu()
  tray.on('double-click', () => createSettingsWindow())
}

function refreshTrayMenu() {
  if (!tray) return
  const cups = store.get('cupPresets') || []
  const today = getToday()
  const pct = Math.round(today.progress * 100)

  const cupItems = cups.map(c => ({
    label: `${c.label} (${c.amount}ml)`,
    click: () => recordDrink(c.amount, c.id)
  }))

  const menu = Menu.buildFromTemplate([
    {
      label: `今日 ${today.total} / ${today.goal} ml  (${pct}%)`,
      enabled: false
    },
    { type: 'separator' },
    {
      label: '我喝了',
      submenu: cupItems
    },
    {
      label: '打开设置',
      click: () => createSettingsWindow()
    },
    { type: 'separator' },
    {
      label: '显示/隐藏桌宠',
      click: () => {
        if (!petWindow) return
        petWindow.isVisible() ? petWindow.hide() : petWindow.show()
      }
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => {
        app.isQuitting = true
        app.quit()
      }
    }
  ])
  tray.setContextMenu(menu)
  tray.setToolTip(`喝水提醒  今日 ${today.total}/${today.goal}ml`)
}

function recordDrink(amount, cupId) {
  logWater(amount, cupId)
  scheduleNextReminder()
  const t = getToday()
  sendToPet('drink-confirmed', { amount, cupId, today: t })
  if (settingsWindow && !settingsWindow.isDestroyed()) {
    settingsWindow.webContents.send('water-updated', t)
  }

  if (t.total >= t.goal && store.get('lastEvolveDate') !== todayKey()) {
    store.set('lastEvolveDate', todayKey())
    sendToPet('evolve', { today: getToday() })
  }

  refreshTrayMenu()
}

function sendToPet(channel, payload) {
  if (petWindow && !petWindow.isDestroyed()) {
    petWindow.webContents.send(channel, payload)
  }
}

function fireReminder() {
  const minutes = store.get('intervalMinutes')
  const soundEnabled = store.get('soundEnabled')

  sendToPet('reminder-fire', { minutes })

  if (Notification.isSupported()) {
    const notification = new Notification({
      title: '该喝水了',
      body: `已经 ${minutes} 分钟没喝了,起来活动一下,补点水`,
      silent: !soundEnabled
    })
    notification.on('click', () => {
      if (petWindow) {
        petWindow.show()
        petWindow.focus()
      }
    })
    notification.show()
  }
}

function scheduleNextReminder() {
  if (reminderTimer) clearTimeout(reminderTimer)
  const minutes = store.get('intervalMinutes')
  const ms = minutes * 60 * 1000
  reminderTimer = setTimeout(() => {
    fireReminder()
    scheduleNextReminder()
  }, ms)
}

function registerIpc() {
  ipcMain.handle('config:get', () => ({
    intervalMinutes: store.get('intervalMinutes'),
    startOnBoot: store.get('startOnBoot'),
    soundEnabled: store.get('soundEnabled')
  }))

  ipcMain.handle('config:set', async (_evt, partial) => {
    if ('intervalMinutes' in partial) {
      store.set('intervalMinutes', partial.intervalMinutes)
      scheduleNextReminder()
    }
    if ('soundEnabled' in partial) {
      store.set('soundEnabled', partial.soundEnabled)
    }
    if ('startOnBoot' in partial) {
      store.set('startOnBoot', partial.startOnBoot)
      try {
        if (partial.startOnBoot) await autoLauncher.enable()
        else await autoLauncher.disable()
      } catch (e) {
        // auto-launch 在开发模式下可能失败,生产环境正常
      }
    }
    return true
  })

  ipcMain.handle('reminder:reset', () => {
    scheduleNextReminder()
    return true
  })

  ipcMain.handle('reminder:test', () => {
    fireReminder()
    return true
  })

  ipcMain.handle('pet:drag-start', () => {
    if (!petWindow) return
    const [winX, winY] = petWindow.getPosition()
    const cursor = screen.getCursorScreenPoint()
    petWindow._dragOffset = { x: cursor.x - winX, y: cursor.y - winY }
    petWindow._dragging = true
  })

  ipcMain.handle('pet:drag-move', () => {
    if (!petWindow || !petWindow._dragging) return
    const cursor = screen.getCursorScreenPoint()
    petWindow.setPosition(cursor.x - petWindow._dragOffset.x, cursor.y - petWindow._dragOffset.y)
  })

  ipcMain.handle('pet:drag-end', () => {
    if (!petWindow) return
    petWindow._dragging = false
    const [x, y] = petWindow.getPosition()
    store.set('petPosition', { x, y })
    emitPetSide()
  })

  ipcMain.handle('settings:open', () => createSettingsWindow())
  ipcMain.handle('settings:close', () => settingsWindow && settingsWindow.close())
  ipcMain.handle('pet:hide', () => petWindow && petWindow.hide())
  ipcMain.handle('app:quit', () => { app.isQuitting = true; app.quit() })

  ipcMain.handle('water:log', (_e, { amount, cupId }) => {
    recordDrink(amount, cupId)
    return getToday()
  })
  ipcMain.handle('water:today', () => getToday())
  ipcMain.handle('water:history', (_e, days) => getHistory(days || 7))
  ipcMain.handle('water:reset-today', () => {
    const t = resetTodayWater()
    refreshTrayMenu()
    if (settingsWindow && !settingsWindow.isDestroyed()) {
      settingsWindow.webContents.send('water-updated', t)
    }
    return t
  })

  ipcMain.handle('cups:get', () => store.get('cupPresets'))
  ipcMain.handle('cups:set', (_e, cups) => {
    store.set('cupPresets', cups)
    refreshTrayMenu()
    return true
  })

  ipcMain.handle('goal:get', () => store.get('dailyGoal'))
  ipcMain.handle('goal:set', (_e, goal) => {
    store.set('dailyGoal', goal)
    refreshTrayMenu()
    if (settingsWindow && !settingsWindow.isDestroyed()) {
      settingsWindow.webContents.send('water-updated', getToday())
    }
    return true
  })
}

app.whenReady().then(async () => {
  await initStore()
  registerIpc()
  createPetWindow()
  createTray()
  scheduleNextReminder()
})

app.on('window-all-closed', (e) => {
  if (!app.isQuitting) e.preventDefault()
})

app.on('before-quit', () => { app.isQuitting = true })
