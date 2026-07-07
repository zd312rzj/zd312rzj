<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import gsap from 'gsap'
import Droplet from './components/Droplet.vue'
import Turtle from './components/Turtle.vue'
import ActionPanel from './components/ActionPanel.vue'
import SpeechBubble from './components/SpeechBubble.vue'
import EvolveOverlay from './components/EvolveOverlay.vue'

const dropletRef = ref(null)
const turtleRef = ref(null)
const evolveRef = ref(null)
const wrapperRef = ref(null)
const stageRef = ref(null)
const floatRef = ref(null)
const panelOpen = ref(false)
const bubbleText = ref('')
const bubbleVisible = ref(false)
const cups = ref([])
const today = ref({ total: 0, goal: 2000, progress: 0 })
const floatText = ref('')
const floatVisible = ref(false)
const side = ref('right')
const form = ref('droplet')
const evolving = ref(false)

let cursorOffset = { x: 0, y: 0 }
let qx = null
let qy = null
let breathingTween = null
let dragging = false
let dragMoved = false
let unsubReminder = null
let unsubDrink = null
let unsubSide = null
let unsubEvolve = null

const currentRef = () => form.value === 'turtle' ? turtleRef.value : dropletRef.value

const onWrapperLeave = () => {
  panelOpen.value = false
  if (qx && qy) { qx(0); qy(0) }
}

const onStageMove = (e) => {
  if (!stageRef.value) return
  const rect = stageRef.value.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  cursorOffset.x = Math.max(-10, Math.min(10, (e.clientX - cx) * 0.12))
  cursorOffset.y = Math.max(-10, Math.min(10, (e.clientY - cy) * 0.12))
  if (qx && qy) { qx(cursorOffset.x); qy(cursorOffset.y) }
}

const setupParallax = () => {
  const c = currentRef()
  if (!c?.rootRef) return
  gsap.set(c.rootRef, { transformOrigin: '50% 60%' })
  qx = gsap.quickTo(c.rootRef, 'x', { duration: 0.45, ease: 'power3.out' })
  qy = gsap.quickTo(c.rootRef, 'y', { duration: 0.45, ease: 'power3.out' })
}

const startBreathing = () => {
  const c = currentRef()
  if (!c?.rootRef) return
  breathingTween = gsap.to(c.rootRef, {
    scale: 1.045, duration: 2, ease: 'sine.inOut',
    repeat: -1, yoyo: true, transformOrigin: '50% 60%'
  })
}

const stopBreathing = () => {
  if (breathingTween) { breathingTween.kill(); breathingTween = null }
}

const playSummonSequence = (minutes) => {
  const c = currentRef()
  if (!c?.rootRef) return
  const el = c.rootRef
  const body = el.querySelector('[data-droplet-body]')

  stopBreathing()
  const tl = gsap.timeline({ onComplete: () => startBreathing() })
  tl.to(el, { scale: 0.82, duration: 0.18, ease: 'power2.in', transformOrigin: '50% 80%' })
    .to(el, { scale: 1.32, duration: 0.22, ease: 'back.out(2.4)', transformOrigin: '50% 80%' })
    .to(el, { scale: 1.08, duration: 0.32, ease: 'elastic.out(1, 0.5)', transformOrigin: '50% 60%' })
    .to(el, { scale: 1, duration: 0.3, ease: 'sine.inOut', transformOrigin: '50% 60%' })

  if (body) {
    tl.to(body, { attr: { 'data-alert': 'on' }, duration: 0 }, 0)
      .to(body, { attr: { 'data-alert': 'off' }, duration: 0 }, 0.6)
  }
  bubbleText.value = '该喝水啦'
  bubbleVisible.value = true
  setTimeout(() => { bubbleVisible.value = false }, 3200)
}

const playDrinkAnim = (amount) => {
  const c = currentRef()
  if (!c?.rootRef) return
  const el = c.rootRef
  gsap.fromTo(el,
    { scale: 1, rotation: 0 },
    {
      scale: 1.2, rotation: -8, duration: 0.25, ease: 'power2.out',
      yoyo: true, repeat: 1,
      onComplete: () => gsap.to(el, { rotation: 0, scale: 1, duration: 0.3, ease: 'elastic.out(1, 0.4)' })
    }
  )
  floatText.value = `+${amount}ml`
  floatVisible.value = true
  if (floatRef.value) {
    gsap.fromTo(floatRef.value,
      { y: 0, opacity: 0, scale: 0.8 },
      {
        y: -38, opacity: 1, scale: 1, duration: 0.6, ease: 'back.out(1.8)',
        onComplete: () => {
          gsap.to(floatRef.value, {
            y: -64, opacity: 0, duration: 0.45, ease: 'power2.in',
            onComplete: () => { floatVisible.value = false }
          })
        }
      }
    )
  }
}

const playEvolveSequence = async () => {
  if (evolving.value) return
  evolving.value = true
  panelOpen.value = false

  const droplet = dropletRef.value?.rootRef
  const overlay = evolveRef.value
  if (!droplet || !overlay) {
    form.value = 'turtle'
    evolving.value = false
    return
  }

  stopBreathing()

  bubbleText.value = '完成今日目标!'
  bubbleVisible.value = true

  const tl = gsap.timeline({
    onComplete: () => {
      evolving.value = false
      setupParallax()
      startBreathing()
      bubbleText.value = '进化了'
      bubbleVisible.value = true
      setTimeout(() => { bubbleVisible.value = false }, 2400)
    }
  })

  tl.to(overlay.rootRef, { opacity: 1, duration: 0.2, ease: 'power2.out' }, 0)
    .fromTo(overlay.ringRef,
      { scale: 0.6, opacity: 0 },
      { scale: 1.6, opacity: 1, duration: 0.8, ease: 'power2.out' }, 0)
    .to(overlay.ringRef, { scale: 2.2, opacity: 0, duration: 0.5, ease: 'power2.in' }, 0.8)

  tl.fromTo(droplet,
    { scale: 1, rotation: 0 },
    {
      scale: 1.08, rotation: 4, duration: 0.12, ease: 'power1.inOut',
      yoyo: true, repeat: 7
    }, 0.1)

  tl.to(overlay.flashRef,
    { scale: 1, opacity: 1, duration: 0.35, ease: 'power3.in' }, 0.9)
    .to(overlay.flashRef,
      { scale: 1.3, duration: 0.6, ease: 'sine.inOut' }, 1.25)

  tl.to(droplet, { scale: 0.6, opacity: 0, duration: 0.25, ease: 'power2.in' }, 1.1)
    .add(() => { form.value = 'turtle' }, 1.4)

  tl.call(() => {
    const turtle = turtleRef.value?.rootRef
    if (turtle) {
      gsap.fromTo(turtle,
        { scale: 0.4, opacity: 0 },
        { scale: 1.15, opacity: 1, duration: 0.55, ease: 'back.out(1.6)' })
      gsap.to(turtle, { scale: 1, duration: 0.4, ease: 'elastic.out(1, 0.5)', delay: 0.55 })
    }
  }, null, 1.45)

  tl.to(overlay.burstRef,
    { scale: 1.6, opacity: 0.85, duration: 0.4, ease: 'power2.out' }, 1.85)
    .to(overlay.burstRef,
      { scale: 2.4, opacity: 0, duration: 0.6, ease: 'power2.in' }, 2.25)

  const sparkles = overlay.getSparkles()
  sparkles.forEach((sp, i) => {
    const angle = (i / sparkles.length) * Math.PI * 2 + Math.random() * 0.4
    const dist = 80 + Math.random() * 40
    tl.fromTo(sp,
      { x: 0, y: 0, opacity: 0, scale: 0.5 },
      {
        x: Math.cos(angle) * dist,
        y: Math.sin(angle) * dist,
        opacity: 1, scale: 1.2,
        duration: 0.55, ease: 'power2.out'
      }, 1.9 + i * 0.02)
      .to(sp,
        { opacity: 0, scale: 0.4, duration: 0.45, ease: 'power2.in' }, 2.4 + i * 0.02)
  })

  tl.to(overlay.rootRef, { opacity: 0, duration: 0.4, ease: 'power2.out' }, 2.7)
}

const handlePick = async (cup) => {
  panelOpen.value = false
  playDrinkAnim(cup.amount)
  const updated = await window.api.water.log(cup.amount, cup.id)
  today.value = updated
}

const handleSnooze = () => {
  panelOpen.value = false
  bubbleText.value = '稍等10分钟'
  bubbleVisible.value = true
  setTimeout(() => { bubbleVisible.value = false }, 1600)
}

const handleSettings = async () => {
  panelOpen.value = false
  await window.api.settings.open()
}

const handleReset = async () => {
  panelOpen.value = false
  const updated = await window.api.water.resetToday()
  today.value = updated

  stopBreathing()
  form.value = 'droplet'
  await nextTick()
  setupParallax()
  startBreathing()

  const droplet = dropletRef.value?.rootRef
  if (droplet) {
    gsap.fromTo(droplet,
      { opacity: 0.75, scale: 0.88 },
      { opacity: 1, scale: 1, duration: 0.38, ease: 'back.out(1.5)' }
    )
  }

  bubbleText.value = '已重置'
  bubbleVisible.value = true
  setTimeout(() => { bubbleVisible.value = false }, 1400)
}

const onPointerDown = async (e) => {
  if (e.button !== 0) return
  dragging = true
  dragMoved = false
  await window.api.pet.dragStart()
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp, { once: true })
}

const onPointerMove = async (e) => {
  if (!dragging) return
  if (Math.abs(e.movementX) + Math.abs(e.movementY) > 0) dragMoved = true
  await window.api.pet.dragMove()
}

const onPointerUp = async () => {
  dragging = false
  window.removeEventListener('pointermove', onPointerMove)
  await window.api.pet.dragEnd()
  setTimeout(() => { dragMoved = false }, 0)
}

const onStageClick = () => {
  if (dragMoved || evolving.value) return
  panelOpen.value = !panelOpen.value
}

const onDoubleClick = () => {
  if (dragMoved || evolving.value) return
  const defaultCup = cups.value.find(c => c.id === 'medium') || cups.value[1] || cups.value[0]
  if (defaultCup) handlePick(defaultCup)
}

onMounted(async () => {
  cups.value = await window.api.cups.get()
  today.value = await window.api.water.today()
  if (today.value.evolved) form.value = 'turtle'

  setupParallax()
  startBreathing()

  unsubReminder = window.api.onReminderFire(({ minutes }) => {
    playSummonSequence(minutes)
  })
  unsubDrink = window.api.onDrinkConfirmed((payload) => {
    if (payload && payload.today) today.value = payload.today
    if (payload && payload.amount) playDrinkAnim(payload.amount)
  })
  unsubSide = window.api.onPetSide((s) => {
    side.value = s === 'left' ? 'left' : 'right'
  })
  unsubEvolve = window.api.onEvolve((payload) => {
    if (payload?.today) today.value = payload.today
    playEvolveSequence()
  })
})

onBeforeUnmount(() => {
  stopBreathing()
  unsubReminder && unsubReminder()
  unsubDrink && unsubDrink()
  unsubSide && unsubSide()
  unsubEvolve && unsubEvolve()
})
</script>

<template>
  <div
    ref="wrapperRef"
    class="pet-wrapper"
    :class="`side-${side}`"
    @mouseleave="onWrapperLeave"
  >
    <div
      ref="stageRef"
      class="pet-stage"
      @pointerdown="onPointerDown"
      @click="onStageClick"
      @dblclick="onDoubleClick"
      @mousemove="onStageMove"
    >
      <SpeechBubble :text="bubbleText" :visible="bubbleVisible" />
      <Droplet v-if="form === 'droplet'" ref="dropletRef" />
      <Turtle v-else ref="turtleRef" />
      <EvolveOverlay ref="evolveRef" />
      <div v-show="floatVisible" ref="floatRef" class="float-text">{{ floatText }}</div>
    </div>

    <ActionPanel
      :open="panelOpen"
      :cups="cups"
      :today="today"
      :side="side"
      @pick="handlePick"
      @snooze="handleSnooze"
      @settings="handleSettings"
      @reset="handleReset"
    />
  </div>
</template>

<style scoped>
.pet-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.pet-stage {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 120px;
  height: 140px;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
}

.side-right .pet-stage { right: 14px; }
.side-left  .pet-stage { left: 14px; }

.pet-stage:active { cursor: grabbing; }

.float-text {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 16px;
  font-weight: 700;
  color: #5FD9CB;
  text-shadow: 0 0 12px rgba(95, 217, 203, 0.6);
  pointer-events: none;
  white-space: nowrap;
  z-index: 20;
}
</style>
