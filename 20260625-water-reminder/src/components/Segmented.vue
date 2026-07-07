<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import gsap from 'gsap'

const props = defineProps({
  modelValue: { type: [Number, String], required: true },
  options: { type: Array, required: true },
  suffix: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const wrapperRef = ref(null)
const indicatorRef = ref(null)
const itemRefs = ref([])

const selectedIndex = computed(() => props.options.findIndex(o => o.value === props.modelValue))

const moveIndicator = () => {
  if (!indicatorRef.value || !wrapperRef.value) return
  const idx = selectedIndex.value
  if (idx < 0) return
  const target = itemRefs.value[idx]
  if (!target) return
  const wrapperRect = wrapperRef.value.getBoundingClientRect()
  const targetRect = target.getBoundingClientRect()
  gsap.to(indicatorRef.value, {
    x: targetRect.left - wrapperRect.left,
    width: targetRect.width,
    duration: 0.45,
    ease: 'back.out(1.4)'
  })
}

watch(() => props.modelValue, async () => {
  await nextTick()
  moveIndicator()
})

const setItemRef = (el, i) => {
  if (el) itemRefs.value[i] = el
  if (i === props.options.length - 1) {
    nextTick(() => moveIndicator())
  }
}

const select = (val) => emit('update:modelValue', val)
</script>

<template>
  <div ref="wrapperRef" class="segmented">
    <div ref="indicatorRef" class="indicator"></div>
    <button
      v-for="(opt, i) in options"
      :key="opt.value"
      :ref="el => setItemRef(el, i)"
      class="seg-item"
      :class="{ 'is-active': opt.value === modelValue }"
      @click="select(opt.value)"
    >
      {{ opt.label }}<span v-if="suffix" class="suffix">{{ suffix }}</span>
    </button>
  </div>
</template>

<style scoped>
.segmented {
  position: relative;
  display: inline-flex;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 3px;
}

.indicator {
  position: absolute;
  top: 3px;
  bottom: 3px;
  left: 0;
  background: linear-gradient(135deg, #4FB7E0, #5FD9CB);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(79, 183, 224, 0.35);
  z-index: 0;
}

.seg-item {
  position: relative;
  z-index: 1;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  transition: color 250ms var(--ease-out-soft);
  min-width: 36px;
}

.seg-item.is-active {
  color: #0d1d28;
  font-weight: 600;
}

.suffix {
  font-size: 10px;
  margin-left: 2px;
  opacity: 0.7;
}
</style>
