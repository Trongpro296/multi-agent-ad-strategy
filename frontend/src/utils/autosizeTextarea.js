// Shared sizing for editable prompts. CSS owns the minimum/maximum viewport bounds.
const states = new WeakMap()

const vAutosizeTextarea = {
  mounted(element, binding) {
    const state = { enabled: binding.value !== false, frame: 0, width: -1, value: undefined }
    state.schedule = () => {
      cancelAnimationFrame(state.frame)
      state.frame = requestAnimationFrame(() => {
        if (!state.enabled || !element.isConnected || element.clientWidth === 0) return
        const scrollTop = element.scrollTop
        element.style.height = 'auto'
        const style = getComputedStyle(element)
        const border = parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth)
        element.style.height = `${element.scrollHeight + border}px`
        element.scrollTop = scrollTop
        state.value = element.value
      })
    }
    state.observer = new ResizeObserver(([entry]) => {
      // Ignore height changes caused by sizing or manual vertical resizing.
      if (entry.contentRect.width !== state.width) {
        state.width = entry.contentRect.width
        state.schedule()
      }
    })
    states.set(element, state)
    element.addEventListener('input', state.schedule)
    window.addEventListener('resize', state.schedule)
    state.observer.observe(element)
    state.schedule()
  },
  updated(element, binding) {
    const state = states.get(element)
    const enabled = binding.value !== false
    if (enabled && (!state.enabled || element.value !== state.value)) state.schedule()
    state.enabled = enabled
  },
  unmounted(element) {
    const state = states.get(element)
    if (!state) return
    cancelAnimationFrame(state.frame)
    state.observer.disconnect()
    element.removeEventListener('input', state.schedule)
    window.removeEventListener('resize', state.schedule)
    states.delete(element)
  }
}

export default vAutosizeTextarea
