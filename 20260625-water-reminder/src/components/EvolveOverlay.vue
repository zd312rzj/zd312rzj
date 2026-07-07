<script setup>
import { ref } from 'vue'

const rootRef = ref(null)
const flashRef = ref(null)
const ringRef = ref(null)
const burstRef = ref(null)
const sparkleRefs = ref([])

const setSparkleRef = (el, i) => { if (el) sparkleRefs.value[i] = el }

defineExpose({
  rootRef, flashRef, ringRef, burstRef,
  getSparkles: () => sparkleRefs.value
})
</script>

<template>
  <div ref="rootRef" class="evolve-overlay">
    <div ref="ringRef" class="evolve-ring"></div>
    <div ref="flashRef" class="evolve-flash"></div>
    <div ref="burstRef" class="evolve-burst"></div>
    <div class="sparkles">
      <div
        v-for="i in 12"
        :key="i"
        :ref="el => setSparkleRef(el, i - 1)"
        class="sparkle"
        :style="{ '--i': i }"
      ></div>
    </div>
  </div>
</template>

<style scoped>
.evolve-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 30;
  opacity: 0;
}

.evolve-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 130px;
  height: 130px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.75);
  box-shadow:
    0 0 40px rgba(255, 255, 255, 0.6),
    inset 0 0 30px rgba(95, 217, 203, 0.55);
  transform: translate(-50%, -50%) scale(0.6);
  opacity: 0;
}

.evolve-flash {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: radial-gradient(circle, #FFFFFF 0%, rgba(255, 255, 255, 0.8) 35%, transparent 75%);
  transform: translate(-50%, -50%) scale(0.3);
  opacity: 0;
  mix-blend-mode: screen;
}

.evolve-burst {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.95) 0%, rgba(127, 224, 240, 0.5) 35%, transparent 70%);
  transform: translate(-50%, -50%) scale(0.2);
  opacity: 0;
}

.sparkles {
  position: absolute;
  inset: 0;
}

.sparkle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #FFFFFF;
  box-shadow: 0 0 12px rgba(127, 224, 240, 0.9);
  transform: translate(-50%, -50%);
  opacity: 0;
}
</style>
