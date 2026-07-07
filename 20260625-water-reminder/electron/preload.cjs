const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('api', {
  config: {
    get: () => ipcRenderer.invoke('config:get'),
    set: (partial) => ipcRenderer.invoke('config:set', partial)
  },
  reminder: {
    reset: () => ipcRenderer.invoke('reminder:reset'),
    test: () => ipcRenderer.invoke('reminder:test')
  },
  pet: {
    dragStart: () => ipcRenderer.invoke('pet:drag-start'),
    dragMove: () => ipcRenderer.invoke('pet:drag-move'),
    dragEnd: () => ipcRenderer.invoke('pet:drag-end'),
    hide: () => ipcRenderer.invoke('pet:hide')
  },
  settings: {
    open: () => ipcRenderer.invoke('settings:open'),
    close: () => ipcRenderer.invoke('settings:close')
  },
  app: {
    quit: () => ipcRenderer.invoke('app:quit')
  },
  water: {
    log: (amount, cupId) => ipcRenderer.invoke('water:log', { amount, cupId }),
    today: () => ipcRenderer.invoke('water:today'),
    history: (days) => ipcRenderer.invoke('water:history', days),
    resetToday: () => ipcRenderer.invoke('water:reset-today')
  },
  cups: {
    get: () => ipcRenderer.invoke('cups:get'),
    set: (cups) => ipcRenderer.invoke('cups:set', cups)
  },
  goal: {
    get: () => ipcRenderer.invoke('goal:get'),
    set: (goal) => ipcRenderer.invoke('goal:set', goal)
  },
  onReminderFire: (cb) => {
    const handler = (_e, payload) => cb(payload)
    ipcRenderer.on('reminder-fire', handler)
    return () => ipcRenderer.removeListener('reminder-fire', handler)
  },
  onDrinkConfirmed: (cb) => {
    const handler = (_e, payload) => cb(payload)
    ipcRenderer.on('drink-confirmed', handler)
    return () => ipcRenderer.removeListener('drink-confirmed', handler)
  },
  onWaterUpdated: (cb) => {
    const handler = (_e, payload) => cb(payload)
    ipcRenderer.on('water-updated', handler)
    return () => ipcRenderer.removeListener('water-updated', handler)
  },
  onPetSide: (cb) => {
    const handler = (_e, side) => cb(side)
    ipcRenderer.on('pet:side', handler)
    return () => ipcRenderer.removeListener('pet:side', handler)
  },
  onEvolve: (cb) => {
    const handler = (_e, payload) => cb(payload)
    ipcRenderer.on('evolve', handler)
    return () => ipcRenderer.removeListener('evolve', handler)
  }
})
