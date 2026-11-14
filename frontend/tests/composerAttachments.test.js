import test from 'node:test'
import assert from 'node:assert/strict'
import { createAttachmentQueue } from '../src/utils/composerAttachments.js'

const file = (name = 'brief.md', type = 'text/markdown') => ({ name, type, size: 1234 })
const deferred = () => { let resolve; const promise = new Promise((done) => { resolve = done }); return { promise, resolve } }
const success = (id = 'server-id') => ({ success: true, attachmentId: id })

test('all selected files are visible immediately, then become ready in order', async () => {
  const first = deferred(); const seen = []
  const queue = createAttachmentQueue(async (session, f) => { seen.push([session, f.name]); return seen.length === 1 ? first.promise : success('second') })
  const done = queue.addFiles([file('a.md'), file('b.json')], 'session-a')
  assert.deepEqual(queue.attachments.value.map((a) => a.status), ['uploading', 'queued'])
  assert.equal(queue.isUploading.value, true)
  first.resolve(success('first')); await done
  assert.deepEqual(queue.readyAttachments.value.map((a) => a.attachmentId), ['first', 'second'])
  assert.deepEqual(seen, [['session-a', 'a.md'], ['session-a', 'b.json']])
  assert.equal(queue.isUploading.value, false)
})

test('failed files stay visible and retry replaces their state without duplicating cards', async () => {
  let attempts = 0
  const queue = createAttachmentQueue(async () => ++attempts === 1 ? { success: false, message: 'Too large' } : success())
  await queue.addFiles([file()], 'session-a')
  assert.equal(queue.hasErrors.value, true)
  assert.equal(queue.readyAttachments.value.length, 0)
  const id = queue.attachments.value[0].id
  assert.equal(queue.attachments.value[0].error, 'Too large')
  await queue.retry(id, 'session-a')
  assert.equal(queue.attachments.value.length, 1)
  assert.equal(queue.attachments.value[0].id, id)
  assert.equal(queue.hasErrors.value, false)
  assert.equal(queue.readyAttachments.value.length, 1)
})

test('an upload exception does not discard other successful files', async () => {
  const queue = createAttachmentQueue(async (session, f) => { if (f.name === 'bad') throw new Error('Offline'); return success() })
  await queue.addFiles([file('bad'), file('good')], 'session-a')
  assert.deepEqual(queue.attachments.value.map((a) => a.status), ['error', 'ready'])
  queue.remove(queue.attachments.value[0].id)
  assert.equal(queue.isUploading.value, false)
  assert.equal(queue.hasErrors.value, false)
  assert.equal(queue.readyAttachments.value.length, 1)
})

test('removing an uploading file never restores it when the response arrives', async () => {
  const result = deferred(); const queue = createAttachmentQueue(() => result.promise)
  const done = queue.addFiles([file()], 'session-a')
  queue.remove(queue.attachments.value[0].id)
  assert.equal(queue.isUploading.value, false)
  result.resolve(success()); await done
  assert.equal(queue.attachments.value.length, 0)
  assert.equal(queue.isUploading.value, false)
})

test('session reset aborts old uploads and ignores their responses and busy-state changes', async () => {
  const old = deferred(); const next = deferred(); let oldSignal
  const queue = createAttachmentQueue((session, f, { signal }) => {
    if (session === 'old') { oldSignal = signal; return old.promise }
    return next.promise
  })
  const oldDone = queue.addFiles([file('old.md')], 'old')
  queue.clear(); assert.equal(oldSignal.aborted, true)
  const nextDone = queue.addFiles([file('new.md')], 'new')
  old.resolve(success('old-id')); await oldDone
  assert.equal(queue.isUploading.value, true)
  assert.deepEqual(queue.attachments.value.map((a) => a.name), ['new.md'])
  assert.equal(queue.readyAttachments.value.length, 0)
  next.resolve(success('new-id')); await nextDone
  assert.equal(queue.readyAttachments.value[0].attachmentId, 'new-id')
})

test('image preview URLs are disposed on remove and clear', async () => {
  const revoked = []
  const queue = createAttachmentQueue(async () => success(), { create: (f) => `blob:${f.name}`, revoke: (url) => revoked.push(url) })
  await queue.addFiles([file('one.png', 'image/png'), file('two.png', 'image/png')], 'session-a')
  assert.equal(queue.attachments.value[0].previewUrl, 'blob:one.png')
  queue.remove(queue.attachments.value[0].id); queue.clear()
  assert.deepEqual(revoked, ['blob:one.png', 'blob:two.png'])
})

test('files with identical names have separate IDs and uploaded legacy entries stay sendable', async () => {
  const queue = createAttachmentQueue(async () => success())
  await queue.addFiles([file(), file()], 'session-a')
  assert.notEqual(queue.attachments.value[0].id, queue.attachments.value[1].id)
  queue.addUploaded({ attachmentId: 'legacy-audio', name: 'recording.wav' })
  assert.equal(queue.readyAttachments.value.length, 3)
})

test('no session means no upload or queued phantom files', async () => {
  let count = 0; const queue = createAttachmentQueue(async () => { count++; return success() })
  await queue.addFiles([file()], null)
  assert.equal(count, 0); assert.equal(queue.attachments.value.length, 0)
})
