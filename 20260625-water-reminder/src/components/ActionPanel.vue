<script setup>
import { ref, watch, nextTick } from 'vue'
import gsap from 'gsap'
import ProgressRing from './ProgressRing.vue'
import CupButton from './CupButton.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  cups: { type: Array, default: () => [] },
  today: { type: Object, default: () => ({ total: 0, goal: 2000, progress: 0 }) },
  side: { type: String, default: 'right' }
})
defineEmits(['pick', 'snooze', 'settings', 'reset'])

const panelRef = ref(null)
const headerRef = ref(null)
const cupRefs = ref([])
const footerRef = ref(null)

const setCupRef = (el, i) => {
  if (el) cupRefs.value[i] = el
}

watch(() => props.open, async (val) => {
  await nextTick()
  if (!panelRef.value) return

  if (val) {
    const fromX = props.side === 'left' ? 28 : -28
    gsap.fromTo(panelRef.value,
      { opacity: 0, x: fromX, scale: 0.92 },
      { opacity: 1, x: 0, scale: 1, duration: 0.42, ease: 'back.out(1.6)' }
    )
    if (headerRef.value) {
      gsap.fromTo(headerRef.value,
        { opacity: 0, y: -6 },
        { opacity: 1, y: 0, duration: 0.32, ease: 'power3.out', delay: 0.08 }
      )
    }
    gsap.fromTo(cupRefs.value,
      { opacity: 0, y: 12 },
      { opacity: 1, y: 0, duration: 0.36, ease: 'back.out(1.4)', stagger: 0.05, delay: 0.14 }
    )
    if (footerRef.value) {
      gsap.fromTo(footerRef.value,
        { opacity: 0, y: 6 },
        { opacity: 1, y: 0, duration: 0.3, ease: 'power3.out', delay: 0.28 }
      )
    }
  } else {
    const toX = props.side === 'left' ? 22 : -22
    gsap.to(panelRef.value, {
      opacity: 0, x: toX, scale: 0.94, duration: 0.22, ease: 'power2.in'
    })
  }
})
</script>

<template>
  <div
    ref="panelRef"
    class="action-panel glass"
    :class="`side-${side}`"
    :style="{ pointerEvents: open ? 'auto' : 'none' }"
  >
    <div ref="headerRef" class="ap-header">
      <div class="ap-meter">
        <ProgressRing :progress="today.progress" :size="48" :stroke="4" />
        <div class="ap-summary">
          <div class="ap-label">今日</div>
          <div class="ap-num">
            <span class="num">{{ today.total }}</span>
            <span class="slash">/</span>
            <span class="goal">{{ today.goal }}</span>
            <span class="unit">ml</span>
          </div>
        </div>
      </div>
      <button class="reset-btn" @click="$emit('reset')">重置</button>
    </div>

    <div class="ap-cups">
      <CupButton
        v-for="(cup, i) in cups"
        :key="cup.id"
        :ref="el => setCupRef(el, i)"
        :label="cup.label"
        :amount="cup.amount"
        @pick="$emit('pick', cup)"
      />
    </div>

    <div ref="footerRef" class="ap-footer">
      <button class="link-btn" @click="$emit('snooze')">稍等10分钟</button>
      <span class="sep">·</span>
      <button class="link-btn" @click="$emit('settings')">设置</button>
    </div>
  </div>
</template>

<style scoped>
.action-panel {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 244px;
  opacity: 0;
  z-index: 10;
}

.action-panel.side-right { left: 12px; }
.action-panel.side-left  { right: 12px; }

.ap-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 2px 4px;
}

.ap-meter {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.ap-summary {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.ap-label {
  font-size: 11px;
  color: var(--color-text-muted, #7A8896);
  line-height: 1;
}

.ap-num {
  display: flex;
  align-items: baseline;
  gap: 3px;
  font-family: var(--font-mono, ui-monospace, monospace);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.ap-num .num {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary, #E8EEF2);
}

.ap-num .slash {
  font-size: 12px;
  color: var(--color-text-muted, #7A8896);
}

.ap-num .goal {
  font-size: 12px;
  color: var(--color-text-secondary, #A7B2BD);
}

.ap-num .unit {
  font-size: 10px;
  color: var(--color-text-muted, #7A8896);
  margin-left: 1px;
}

.reset-btn {
  flex: 0 0 auto;
  height: 24px;
  padding: 0 8px;
  border: 1px solid rgba(95, 217, 203, 0.22);
  border-radius: 8px;
  color: rgba(232, 238, 242, 0.74);
  background: rgba(255, 255, 255, 0.06);
  font-size: 11px;
  line-height: 22px;
  transition:
    color 180ms cubic-bezier(0.34, 1.56, 0.64, 1),
    border-color 180ms cubic-bezier(0.34, 1.56, 0.64, 1),
    background 180ms cubic-bezier(0.34, 1.56, 0.64, 1),
    transform 180ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.reset-btn:hover {
  color: #E8EEF2;
  border-color: rgba(95, 217, 203, 0.46);
  background: rgba(95, 217, 203, 0.12);
  transform: translateY(-1px);
}

.reset-btn:active {
  transform: translateY(0) scale(0.96);
}

.ap-cups {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.ap-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 4px 0 2px;
  opacity: 0;
}

.link-btn {
  font-size: 11px;
  color: var(--color-text-muted, #7A8896);
  padding: 2px 4px;
  border-radius: 4px;
  transition: color 180ms ease;
}

.link-btn:hover {
  color: var(--color-text-primary, #E8EEF2);
}

.sep {
  color: var(--color-text-muted, #7A8896);
  font-size: 11px;
  opacity: 0.5;
}
</style>
