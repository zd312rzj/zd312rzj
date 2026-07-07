<script setup>
import { ref } from 'vue'
import gsap from 'gsap'

const props = defineProps({
  label: { type: String, default: '' },
  amount: { type: Number, required: true }
})
defineEmits(['pick'])

const waterRef = ref(null)
const rootRef = ref(null)

const onEnter = () => {
  if (!waterRef.value) return
  gsap.to(waterRef.value, { y: -14, duration: 0.6, ease: 'back.out(1.4)' })
}

const onLeave = () => {
  if (!waterRef.value) return
  gsap.to(waterRef.value, { y: 0, duration: 0.4, ease: 'power3.out' })
}

const onClick = () => {
  if (rootRef.value) {
    gsap.fromTo(rootRef.value,
      { scale: 1 },
      { scale: 0.88, duration: 0.1, ease: 'power2.in', yoyo: true, repeat: 1 }
    )
  }
  if (waterRef.value) {
    gsap.fromTo(waterRef.value,
      { y: -22 },
      { y: 0, duration: 0.45, ease: 'bounce.out' }
    )
  }
}
</script>

<template>
  <button
    ref="rootRef"
    class="cup-btn"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
    @click="$emit('pick'); onClick()"
  >
    <div class="cup-icon">
      <svg width="28" height="34" viewBox="0 0 28 34">
        <defs>
          <linearGradient :id="`cup-w-${amount}`" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#4FB7E0"/>
            <stop offset="100%" stop-color="#5FD9CB"/>
          </linearGradient>
          <clipPath :id="`cup-clip-${amount}`">
            <path d="M5 6 L 23 6 L 21 30 Q 21 32 19 32 L 9 32 Q 7 32 7 30 Z"/>
          </clipPath>
        </defs>
        <g :clip-path="`url(#cup-clip-${amount})`">
          <rect x="0" y="14" width="28" height="22" :fill="`url(#cup-w-${amount})`" ref="waterRef"/>
        </g>
        <path
          d="M5 6 L 23 6 L 21 30 Q 21 32 19 32 L 9 32 Q 7 32 7 30 Z"
          fill="none"
          stroke="rgba(255,255,255,0.55)"
          stroke-width="1.4"
          stroke-linejoin="round"
        />
        <line x1="6" y1="9" x2="22" y2="9" stroke="rgba(255,255,255,0.35)" stroke-width="0.8" />
      </svg>
    </div>
    <div class="cup-amount">{{ amount }}</div>
    <div class="cup-label">{{ label }}</div>
  </button>
</template>

<style scoped>
.cup-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 4px 5px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  min-width: 50px;
  transition: background-color 200ms var(--ease-out-soft, ease), border-color 200ms var(--ease-out-soft, ease), transform 220ms var(--ease-spring, cubic-bezier(0.34,1.56,0.64,1));
}

.cup-btn:hover {
  background: rgba(79, 183, 224, 0.12);
  border-color: rgba(79, 183, 224, 0.35);
  transform: translateY(-2px);
}

.cup-btn:active {
  transform: translateY(0) scale(0.96);
}

.cup-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  filter: drop-shadow(0 2px 4px rgba(79, 183, 224, 0.3));
}

.cup-amount {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-primary, #E8EEF2);
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono, ui-monospace, monospace);
  line-height: 1;
}

.cup-label {
  font-size: 9px;
  color: var(--color-text-muted, #7A8896);
  line-height: 1;
}
</style>
