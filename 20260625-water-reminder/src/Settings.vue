<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import gsap from 'gsap'
import Segmented from './components/Segmented.vue'
import Toggle from './components/Toggle.vue'
import ProgressRing from './components/ProgressRing.vue'
import BarChart from './components/BarChart.vue'

const tab = ref('settings')
const tabs = [
  { value: 'settings', label: '设置' },
  { value: 'today', label: '今日' },
  { value: 'history', label: '历史' }
]

const config = ref({
  intervalMinutes: 45,
  startOnBoot: false,
  soundEnabled: true
})

const intervals = [
  { value: 30, label: '30' },
  { value: 45, label: '45' },
  { value: 60, label: '60' },
  { value: 90, label: '90' }
]

const cups = ref([])
const goal = ref(2000)
const today = ref({ total: 0, goal: 2000, progress: 0, entries: [] })
const history = ref({ days: [], goal: 2000 })

const cardRef = ref(null)
const viewRef = ref(null)
const loaded = ref(false)
let unsubWater = null

onMounted(async () => {
  const cfg = await window.api.config.get()
  config.value = { ...config.value, ...cfg }
  cups.value = await window.api.cups.get()
  goal.value = await window.api.goal.get()
  today.value = await window.api.water.today()
  history.value = await window.api.water.history(7)
  loaded.value = true

  await nextTick()
  gsap.fromTo(cardRef.value,
    { opacity: 0, y: 16, scale: 0.96 },
    { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: 'back.out(1.4)' }
  )

  unsubWater = window.api.onWaterUpdated((t) => {
    today.value = t
    refreshHistory()
  })
})

const refreshHistory = async () => {
  history.value = await window.api.water.history(7)
}

watch(tab, async () => {
  await nextTick()
  if (!viewRef.value) return
  gsap.fromTo(viewRef.value,
    { opacity: 0, y: 10 },
    { opacity: 1, y: 0, duration: 0.36, ease: 'power3.out' }
  )
  if (tab.value === 'today' || tab.value === 'history') {
    today.value = await window.api.water.today()
    history.value = await window.api.water.history(7)
  }
})

watch(() => config.value.intervalMinutes, (v) => {
  if (!loaded.value) return
  window.api.config.set({ intervalMinutes: v })
})
watch(() => config.value.startOnBoot, (v) => {
  if (!loaded.value) return
  window.api.config.set({ startOnBoot: v })
})
watch(() => config.value.soundEnabled, (v) => {
  if (!loaded.value) return
  window.api.config.set({ soundEnabled: v })
})

const updateCup = (idx, val) => {
  const n = parseInt(val) || 0
  if (n < 0 || n > 9999) return
  cups.value[idx].amount = n
  window.api.cups.set(JSON.parse(JSON.stringify(cups.value)))
}

const updateGoal = (val) => {
  const n = parseInt(val) || 0
  if (n < 100 || n > 10000) return
  goal.value = n
  window.api.goal.set(n)
}

const fmtTime = (ts) => {
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const entriesReversed = computed(() => [...(today.value.entries || [])].reverse())

const weekAvg = computed(() => {
  if (!history.value.days.length) return 0
  const sum = history.value.days.reduce((s, d) => s + d.total, 0)
  return Math.round(sum / history.value.days.length)
})

const weekDoneDays = computed(() => {
  return history.value.days.filter(d => d.total >= history.value.goal).length
})

const close = () => window.api.settings.close()
const quit = () => window.api.app.quit()
const testReminder = () => window.api.reminder.test()
</script>

<template>
  <div class="settings-bg">
    <div ref="cardRef" class="settings-card glass" style="opacity: 0">
      <div class="title-bar drag-region">
        <div class="title">
          <span class="title-icon"></span>
          <span>喝水提醒</span>
        </div>
        <button class="close-btn no-drag" @click="close" aria-label="关闭">
          <svg width="14" height="14" viewBox="0 0 14 14">
            <path d="M3 3 L 11 11 M 11 3 L 3 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
        </button>
      </div>

      <div class="tab-bar no-drag">
        <Segmented v-model="tab" :options="tabs" />
      </div>

      <div ref="viewRef" class="view-area">
        <div v-if="tab === 'settings'" class="view">
          <div class="row">
            <div class="row-label">
              <div class="label-main">提醒间隔</div>
              <div class="label-sub">每隔多久叫你喝一次</div>
            </div>
            <Segmented v-model="config.intervalMinutes" :options="intervals" suffix="分钟" />
          </div>

          <div class="row">
            <div class="row-label">
              <div class="label-main">每日目标</div>
              <div class="label-sub">推荐 1500-2500ml</div>
            </div>
            <div class="num-input">
              <input
                type="number"
                :value="goal"
                min="100" max="10000" step="100"
                @change="e => updateGoal(e.target.value)"
              />
              <span class="unit">ml</span>
            </div>
          </div>

          <div class="row">
            <div class="row-label">
              <div class="label-main">杯型容量</div>
              <div class="label-sub">点击数值修改,单位 ml</div>
            </div>
          </div>

          <div class="cups-grid">
            <div v-for="(c, i) in cups" :key="c.id" class="cup-edit">
              <div class="cup-edit-label">{{ c.label }}</div>
              <div class="num-input compact">
                <input
                  type="number"
                  :value="c.amount"
                  min="0" max="9999" step="10"
                  @change="e => updateCup(i, e.target.value)"
                />
                <span class="unit">ml</span>
              </div>
            </div>
          </div>

          <div class="row">
            <div class="row-label">
              <div class="label-main">开机自启</div>
              <div class="label-sub">登录系统时自动唤起小桌宠</div>
            </div>
            <Toggle v-model="config.startOnBoot" />
          </div>

          <div class="row">
            <div class="row-label">
              <div class="label-main">提醒声音</div>
              <div class="label-sub">使用系统通知音</div>
            </div>
            <Toggle v-model="config.soundEnabled" />
          </div>
        </div>

        <div v-else-if="tab === 'today'" class="view today-view">
          <div class="today-hero">
            <ProgressRing :progress="today.progress" :size="140" :stroke="10" :showLabel="false" />
            <div class="hero-center">
              <div class="hero-num">{{ today.total }}</div>
              <div class="hero-unit">ml / {{ today.goal }}</div>
            </div>
          </div>

          <div class="today-stats">
            <div class="stat">
              <div class="stat-num">{{ today.entries?.length || 0 }}</div>
              <div class="stat-label">次数</div>
            </div>
            <div class="stat">
              <div class="stat-num">{{ Math.round(today.progress * 100) }}<span class="pct">%</span></div>
              <div class="stat-label">完成度</div>
            </div>
            <div class="stat">
              <div class="stat-num">{{ Math.max(0, today.goal - today.total) }}</div>
              <div class="stat-label">还差(ml)</div>
            </div>
          </div>

          <div class="timeline">
            <div class="timeline-title">今日记录</div>
            <div v-if="!today.entries?.length" class="empty">
              今天还没喝水,从小桌宠选个杯子开始吧
            </div>
            <div v-else class="timeline-list">
              <div v-for="e in entriesReversed" :key="e.time" class="t-entry">
                <span class="t-time">{{ fmtTime(e.time) }}</span>
                <span class="t-dot"></span>
                <span class="t-amount">+{{ e.amount }}<span class="t-unit">ml</span></span>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="tab === 'history'" class="view history-view">
          <div class="history-summary">
            <div class="hs-item">
              <div class="hs-num">{{ weekAvg }}<span class="hs-unit">ml</span></div>
              <div class="hs-label">7日均值</div>
            </div>
            <div class="hs-item">
              <div class="hs-num">{{ weekDoneDays }}<span class="hs-unit">/7</span></div>
              <div class="hs-label">达标天数</div>
            </div>
          </div>
          <BarChart :data="history.days" :goal="history.goal" :height="170" />
        </div>
      </div>

      <div class="footer">
        <button class="test-btn" @click="testReminder">立即测试一次</button>
        <button class="quit-btn" @click="quit">退出应用</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-bg {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.settings-card {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  overflow: hidden;
}

.title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px 4px;
}

.title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.title-icon {
  width: 16px;
  height: 18px;
  background: linear-gradient(180deg, #4FB7E0, #5FD9CB);
  clip-path: path('M8 1 C 12 6, 15 10, 15 13 a 7 7 0 0 1 -14 0 C 1 10, 4 6, 8 1 Z');
}

.close-btn {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--color-text-secondary);
  transition: background-color 180ms var(--ease-out-soft), color 180ms var(--ease-out-soft);
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-primary);
}

.tab-bar {
  padding: 6px 18px 10px;
  display: flex;
  justify-content: center;
}

.view-area {
  flex: 1;
  overflow-y: auto;
  padding: 4px 18px;
}

.view-area::-webkit-scrollbar { width: 4px; }
.view-area::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

.view {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border-subtle);
  gap: 12px;
}

.row:last-child { border-bottom: none; }

.row-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.label-main {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.label-sub {
  font-size: 11px;
  color: var(--color-text-muted);
}

.num-input {
  display: inline-flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 4px 10px;
  gap: 4px;
  border: 1px solid transparent;
  transition: border-color 180ms;
}

.num-input:focus-within {
  border-color: rgba(79, 183, 224, 0.5);
  background: rgba(79, 183, 224, 0.08);
}

.num-input input {
  width: 56px;
  background: transparent;
  border: none;
  outline: none;
  color: var(--color-text-primary);
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 13px;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.num-input input::-webkit-outer-spin-button,
.num-input input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.num-input .unit {
  font-size: 10px;
  color: var(--color-text-muted);
}

.num-input.compact input { width: 44px; font-size: 12px; }
.num-input.compact { padding: 3px 8px; }

.cups-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 0 0 12px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.cup-edit {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  background: rgba(255, 255, 255, 0.025);
  border-radius: 8px;
}

.cup-edit-label {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.today-view, .history-view {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 4px;
}

.today-hero {
  position: relative;
  width: 140px;
  height: 140px;
  margin: 6px auto 0;
}

.hero-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.hero-num {
  font-size: 30px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: var(--font-mono, ui-monospace, monospace);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.hero-unit {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-mono, ui-monospace, monospace);
}

.today-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 10px 0;
  border-top: 1px solid var(--color-border-subtle);
  border-bottom: 1px solid var(--color-border-subtle);
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: var(--font-mono, ui-monospace, monospace);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.stat-num .pct {
  font-size: 11px;
  color: var(--color-text-muted);
  font-weight: 500;
  margin-left: 1px;
}

.stat-label {
  font-size: 10px;
  color: var(--color-text-muted);
}

.timeline-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.empty {
  font-size: 12px;
  color: var(--color-text-muted);
  padding: 16px;
  text-align: center;
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
}

.timeline-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 160px;
  overflow-y: auto;
}

.t-entry {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  background: rgba(255,255,255,0.025);
  border-radius: 6px;
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 12px;
}

.t-time { color: var(--color-text-muted); font-variant-numeric: tabular-nums; }

.t-dot {
  width: 4px; height: 4px; border-radius: 50%;
  background: linear-gradient(135deg, #4FB7E0, #5FD9CB);
}

.t-amount {
  margin-left: auto;
  color: var(--color-text-primary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.t-unit { font-size: 10px; color: var(--color-text-muted); margin-left: 1px; }

.history-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding-bottom: 6px;
}

.hs-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  background: rgba(255,255,255,0.025);
  border-radius: 10px;
  gap: 2px;
}

.hs-num {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: var(--font-mono, ui-monospace, monospace);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.hs-unit {
  font-size: 11px;
  color: var(--color-text-muted);
  font-weight: 500;
  margin-left: 2px;
}

.hs-label {
  font-size: 10px;
  color: var(--color-text-muted);
}

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px 16px;
}

.test-btn {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  color: #0d1d28;
  background: linear-gradient(135deg, #4FB7E0, #5FD9CB);
  transition: all 200ms var(--ease-out-soft);
  box-shadow: 0 2px 8px rgba(79, 183, 224, 0.3);
}

.test-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 183, 224, 0.45);
}

.test-btn:active {
  transform: translateY(0) scale(0.97);
}

.quit-btn {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--color-border-subtle);
  transition: all 180ms var(--ease-out-soft);
}

.quit-btn:hover {
  background: rgba(255, 100, 100, 0.16);
  color: #FF8A8A;
  border-color: rgba(255, 100, 100, 0.3);
}
</style>
