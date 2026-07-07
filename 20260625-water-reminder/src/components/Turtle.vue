<script setup>
import { ref } from 'vue'
import turtleSrc from '../assets/turtle.png'

const rootRef = ref(null)
defineExpose({ rootRef })
</script>

<template>
  <div ref="rootRef" class="turtle-wrap">
    <img :src="turtleSrc" alt="" class="turtle-img" draggable="false" />
  </div>
</template>

<style scoped>
.turtle-wrap {
  width: 124px;
  height: 124px;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: drop-shadow(0 7px 18px rgba(38, 88, 138, 0.5))
          drop-shadow(0 3px 8px rgba(95, 217, 203, 0.28));
}

.turtle-img {
  width: 118px;
  height: 118px;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
  user-select: none;
  pointer-events: none;
}
</style>
