<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import gsap from 'gsap'

const props = defineProps({
  data: { type: Array, default: () => [] },
  goal: { type: Number, default: 2000 },
  height: { type: Number, default: 140 }
})

const maxValue = computed(() => {
  const m = Math.max(props.goal, ...props.data.map(d => d.total), 100)
  return m * 1.08
})

const barRefs = ref([])
const setBarRef = (el, i) => { if (el) barRefs.value[i] = el }

const animate = () => {
  if (!barRefs.value.length) return
  gsap.fromTo(barRefs.value,
    { scaleY: 0, transformOrigin: 'bottom' },
    { scaleY: 1, duration: 0.7, ease: 'back.out(1.4)', stagger: 0.06 }
  )
}

onMounted(animate)
watch(() => props.data, () => requestAnimationFrame(animate), { deep: true })

const barHeight = (v) => `${(v / maxValue.value) * 100}%`
const goalPct = computed(() => `${(props.goal / maxValue.value) * 100}%`)
</script>

<template>
  <div class="chart" :style="{ height: height + 'px' }">
    <div class="chart-canvas">
      <div class="goal-line" :style="{ bottom: goalPct }">
        <span class="goal-tag">{{ goal }}ml</span>
      </div>
      <div class="bars">
        <div
          v-for="(d, i) in data"
          :key="d.date"
          class="bar-col"
        >
          <div class="bar-stack">
            <div
              :ref="el => setBarRef(el, i)"
              class="bar"
              :class="{ 'is-today': d.isToday, 'is-done': d.total >= goal }"
              :style="{ height: barHeight(d.total) }"
            >
              <div class="bar-fill"></div>
              <div v-if="d.total > 0" class="bar-tip">{{ d.total }}</div>
            </div>
          </div>
          <div class="bar-label" :class="{ 'is-today': d.isToday }">{{ d.label }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.chart-canvas {
  flex: 1;
  position: relative;
  padding-top: 14px;
}

.goal-line {
  position: absolute;
  left: 4px;
  right: 4px;
  height: 1px;
  background: repeating-linear-gradient(90deg, rgba(95,217,203,0.45) 0 4px, transparent 4px 8px);
  z-index: 1;
}

.goal-tag {
  position: absolute;
  right: 0;
  top: -8px;
  font-size: 9px;
  color: rgba(95,217,203,0.85);
  background: rgba(13, 18, 24, 0.7);
  padding: 1px 4px;
  border-radius: 3px;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.bars {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  height: 100%;
  position: relative;
  z-index: 2;
}

.bar-col {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  min-width: 0;
}

.bar-stack {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: stretch;
  position: relative;
}

.bar {
  width: 100%;
  position: relative;
  border-radius: 4px 4px 1px 1px;
  overflow: hidden;
  min-height: 1px;
}

.bar-fill {
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #4FB7E0 0%, #5FD9CB 100%);
  opacity: 0.55;
}

.bar.is-today .bar-fill {
  opacity: 0.95;
  box-shadow: 0 0 12px rgba(95, 217, 203, 0.5);
}

.bar.is-done .bar-fill {
  background: linear-gradient(180deg, #5FD9CB 0%, #7BE8B8 100%);
}

.bar-tip {
  position: absolute;
  top: -16px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 9px;
  color: var(--color-text-secondary, #A7B2BD);
  font-family: var(--font-mono, ui-monospace, monospace);
  white-space: nowrap;
}

.bar.is-today .bar-tip {
  color: #5FD9CB;
  font-weight: 600;
}

.bar-label {
  margin-top: 6px;
  font-size: 10px;
  text-align: center;
  color: var(--color-text-muted, #7A8896);
  font-family: var(--font-mono, ui-monospace, monospace);
}

.bar-label.is-today {
  color: var(--color-text-primary, #E8EEF2);
  font-weight: 600;
}
</style>
