<script setup>
import { ref, watch, nextTick } from 'vue'
import gsap from 'gsap'

const props = defineProps({
  text: { type: String, default: '' },
  visible: { type: Boolean, default: false }
})

const bubbleRef = ref(null)

watch(() => props.visible, async (val) => {
  await nextTick()
  if (!bubbleRef.value) return

  if (val) {
    gsap.fromTo(bubbleRef.value,
      { opacity: 0, y: 10, scale: 0.82 },
      { opacity: 1, y: 0, scale: 1, duration: 0.45, ease: 'back.out(2)' }
    )
  } else {
    gsap.to(bubbleRef.value, {
      opacity: 0,
      y: -4,
      scale: 0.92,
      duration: 0.22,
      ease: 'power2.in'
    })
  }
})
</script>

<template>
  <div
    v-if="text"
    ref="bubbleRef"
    class="speech-bubble glass"
    :style="{ opacity: 0 }"
  >
    {{ text }}
    <span class="tail"></span>
  </div>
</template>

<style scoped>
.speech-bubble {
  position: absolute;
  top: 4px;
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
  border-radius: 14px;
  white-space: nowrap;
  z-index: 20;
  letter-spacing: 0.5px;
  pointer-events: none;
}

.tail {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 8px;
  height: 8px;
  background: var(--color-bg-glass);
  border-right: 1px solid var(--color-border-subtle);
  border-bottom: 1px solid var(--color-border-subtle);
}
</style>
