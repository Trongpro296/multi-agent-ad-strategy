import { computed, ref } from 'vue'

// Keep browser Files until send/remove so a failed upload can be retried.
// Session resets invalidate in-flight responses before they can enter a new draft.
export function createAttachmentQueue(upload, previews = {
  create: (file) => URL.createObjectURL(file),
  revoke: (url) => URL.revokeObjectURL(url),
}) {
  const attachments = ref([])
  const isUploading = ref(false)
  let nextId = 0
  let generation = 0
  let controller = null
  const readyAttachments = computed(() => attachments.value.filter((item) => item.status === 'ready'))
  const hasErrors = computed(() => attachments.value.some((item) => item.status === 'error'))

  const dispose = (item) => { if (item.previewUrl) previews.revoke(item.previewUrl) }
  const clear = () => {
    generation += 1
    controller?.abort()
    controller = null
    attachments.value.forEach(dispose)
    attachments.value = []
    isUploading.value = false
  }
  const remove = (id) => {
    const item = attachments.value.find((entry) => entry.id === id)
    if (item) dispose(item)
    attachments.value = attachments.value.filter((entry) => entry.id !== id)
    if (!attachments.value.length) clear()
  }
  const run = async (items, sessionId) => {
    if (!sessionId || isUploading.value || !items.length) return
    const ticket = generation
    const active = new AbortController()
    controller = active
    isUploading.value = true
    try {
      for (const item of items) {
        if (ticket !== generation) break
        if (!attachments.value.some((entry) => entry.id === item.id)) continue
        // Use the reactive entry: asynchronous status changes must update Vue.
        const entry = attachments.value.find((value) => value.id === item.id)
        entry.status = 'uploading'
        entry.error = ''
        try {
          const result = await upload(sessionId, item.file, { signal: active.signal })
          if (ticket !== generation) break
          const current = attachments.value.find((value) => value.id === item.id)
          if (!current) continue
          if (!result?.success || !result?.attachmentId) throw new Error(result?.message || 'Upload failed')
          Object.assign(current, { attachmentId: result.attachmentId, name: result.name || current.name,
            mimeType: result.mimeType || current.mimeType, size: result.size ?? current.size, status: 'ready' })
        } catch (error) {
          if (ticket !== generation) break
          const current = attachments.value.find((value) => value.id === item.id)
          if (current) Object.assign(current, { status: 'error', error: error?.message || 'Upload failed' })
        }
      }
    } finally {
      if (ticket === generation) { isUploading.value = false; controller = null }
    }
  }
  const addFiles = async (files, sessionId) => {
    if (!sessionId || isUploading.value) return
    const items = Array.from(files || []).map((file) => ({
      id: `draft-file-${++nextId}`, name: file.name || 'upload', size: file.size,
      mimeType: file.type || '', file, status: 'queued', error: '', attachmentId: null,
      previewUrl: file.type?.startsWith('image/') ? previews.create(file) : null,
    }))
    attachments.value.push(...items)
    await run(items, sessionId)
  }
  const retry = async (id, sessionId) => {
    const item = attachments.value.find((entry) => entry.id === id)
    if (!item || item.status !== 'error' || isUploading.value) return
    await run([item], sessionId)
  }
  const addUploaded = (result) => {
    attachments.value.push({ ...result, id: `draft-file-${++nextId}`, status: 'ready', error: '' })
  }
  return { attachments, readyAttachments, isUploading, hasErrors, addFiles, retry, remove, clear, addUploaded }
}
