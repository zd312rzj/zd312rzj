<script setup>
const props = defineProps({
  modelValue: { type: Boolean, required: true }
})
const emit = defineEmits(['update:modelValue'])

const toggle = () => emit('update:modelValue', !props.modelValue)
</script>

<template>
  <button
    class="toggle"
    :class="{ 'is-on': modelValue }"
    role="switch"
    :aria-checked="modelValue"
    @click="toggle"
  >
    <span class="thumb"></span>
  </button>
</template>

<style scoped>
.toggle {
  position: relative;
  width: 40px;
  height: 22px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  transition: background-color 280ms var(--ease-in-out-soft);
  flex-shrink: 0;
}

.toggle.is-on {
  background: linear-gradient(135deg, #4FB7E0, #5FD9CB);
}

.thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
  transition: transform 350ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toggle.is-on .thumb {
  transform: translateX(18px);
}
</style>
