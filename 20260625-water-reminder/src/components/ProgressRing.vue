<script setup>
import { computed, watch, ref } from 'vue'
import gsap from 'gsap'

const props = defineProps({
  progress: { type: Number, default: 0 },
  size: { type: Number, default: 60 },
  stroke: { type: Number, default: 5 },
  showLabel: { type: Boolean, default: true }
})

const animated = ref(0)
const radius = computed(() => (props.size - props.stroke) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const offset = computed(() => circumference.value * (1 - Math.min(1, Math.max(0, animated.value))))
const pct = computed(() => Math.round(animated.value * 100))

watch(() => props.progress, (v) => {
  gsap.to(animated, { value: v, duration: 0.9, ease: 'power3.out' })
}, { immediate: true })
</script>

<template>
  <div class="ring-wrap" :style="{ width: size + 'px', height: size + 'px' }">
    <svg :width="size" :height="size" class="ring-svg">
      <defs>
        <linearGradient :id="`ring-grad-${size}`" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#4FB7E0"/>
          <stop offset="100%" stop-color="#5FD9CB"/>
        </linearGradient>
      </defs>
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        stroke="rgba(255,255,255,0.08)"
        :stroke-width="stroke"
      />
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="`url(#ring-grad-${size})`"
        :stroke-width="stroke"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="offset"
        :transform="`rotate(-90 ${size / 2} ${size / 2})`"
      />
    </svg>
    <div v-if="showLabel" class="ring-label">
      <span class="ring-num">{{ pct }}</span>
      <span class="ring-unit">%</span>
    </div>
  </div>
</template>

<style scoped>
.ring-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.ring-svg {
  display: block;
}

.ring-label {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 1px;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.ring-num {
  font-size: 0.9em;
  font-weight: 600;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.ring-unit {
  font-size: 0.5em;
  color: var(--color-text-muted);
  line-height: 1;
}
</style>
