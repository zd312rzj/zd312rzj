<script setup>
import { ref } from 'vue'

const rootRef = ref(null)
defineExpose({ rootRef })
</script>

<template>
  <svg
    ref="rootRef"
    viewBox="0 0 120 140"
    width="110"
    height="130"
    xmlns="http://www.w3.org/2000/svg"
    class="droplet-svg"
  >
    <defs>
      <linearGradient id="dropletGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#4FB7E0" />
        <stop offset="100%" stop-color="#5FD9CB" />
      </linearGradient>
      <linearGradient id="dropletAlertGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#FFB85C" />
        <stop offset="100%" stop-color="#FF7A45" />
      </linearGradient>
      <radialGradient id="hilight" cx="0.35" cy="0.3" r="0.35">
        <stop offset="0%" stop-color="rgba(255,255,255,0.85)" />
        <stop offset="100%" stop-color="rgba(255,255,255,0)" />
      </radialGradient>
      <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="6" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>

    <ellipse cx="60" cy="128" rx="34" ry="5" fill="rgba(79,183,224,0.25)" />

    <g filter="url(#softGlow)">
      <path
        data-droplet-body
        data-alert="off"
        d="M60 14
           C 78 38, 96 62, 96 84
           a 36 36 0 0 1 -72 0
           C 24 62, 42 38, 60 14 Z"
        fill="url(#dropletGrad)"
        class="droplet-body"
      />
      <ellipse
        cx="48"
        cy="55"
        rx="14"
        ry="22"
        fill="url(#hilight)"
        transform="rotate(-20 48 55)"
      />
      <circle cx="50" cy="78" r="3.5" fill="rgba(20,40,60,0.7)" class="eye eye-left" />
      <circle cx="70" cy="78" r="3.5" fill="rgba(20,40,60,0.7)" class="eye eye-right" />
      <path
        d="M 54 90 Q 60 95 66 90"
        stroke="rgba(20,40,60,0.55)"
        stroke-width="2"
        fill="none"
        stroke-linecap="round"
      />
    </g>
  </svg>
</template>

<style scoped>
.droplet-svg {
  display: block;
  overflow: visible;
  will-change: transform;
}

.droplet-body {
  transition: fill 400ms cubic-bezier(0.65, 0, 0.35, 1);
}

.droplet-body[data-alert='on'] {
  fill: url(#dropletAlertGrad);
}

.eye {
  transform-origin: center;
  animation: blink 5.5s cubic-bezier(0.65, 0, 0.35, 1) infinite;
}

.eye-right {
  animation-delay: 0.08s;
}

@keyframes blink {
  0%, 92%, 100% { transform: scaleY(1); }
  94%, 96% { transform: scaleY(0.1); }
}
</style>
