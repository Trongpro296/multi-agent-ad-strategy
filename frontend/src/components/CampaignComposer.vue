<template>
  <section class="campaign-composer" :class="{ 'is-dragging': dragActive, 'is-highlighted': highlight, 'is-empty': !modelValue && !attachments.length, 'is-locked-empty': disabled && !modelValue && !attachments.length }"
    :aria-label="$t('launch.composer_label')" @dragenter="dragEnter" @dragover="dragOver"
    @dragleave="dragLeave" @drop="dropFiles">
    <div v-if="attachments.length" class="composer-files" :aria-label="$t('launch.composer_files')">
      <article v-for="item in attachments" :key="item.id" class="composer-file"
        :class="{ 'has-error': item.status === 'error' }" :aria-busy="item.status === 'uploading'">
        <button v-if="item.previewUrl" class="file-preview" type="button"
          :aria-label="$t('launch.composer_preview', { name: item.name })" @click="$emit('preview', item)">
          <img :src="item.previewUrl" :alt="item.name" />
        </button>
        <span v-else class="file-symbol" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.6">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>
          </svg>
        </span>
        <div class="file-details">
          <span class="file-title" :title="item.name">{{ item.name }}</span>
          <span class="file-meta">{{ fileType(item) }} · {{ fileSize(item.size) }}</span>
          <span class="file-state" :title="item.error || ''">
            <span v-if="item.status === 'uploading'" class="upload-spinner" aria-hidden="true"></span>
            {{ $t(`launch.composer_file_${item.status}`) }}
          </span>
          <span v-if="item.status === 'error'" class="file-error-detail" :title="item.error">{{ item.error }}</span>
          <button v-if="item.status === 'error'" class="file-retry" type="button"
            :disabled="uploadDisabled || uploading" @click="$emit('retry', item.id)">{{ $t('launch.composer_retry') }}</button>
        </div>
        <button class="file-remove" type="button" :disabled="disabled"
          :aria-label="$t('launch.composer_remove', { name: item.name })" @click="$emit('remove', item.id)">×</button>
      </article>
    </div>
    <textarea ref="input" v-autosize-textarea class="composer-textarea" :value="modelValue"
      :disabled="disabled" :placeholder="$t('launch.enter_prompt')" :aria-label="$t('launch.enter_prompt')"
      :aria-describedby="hintId" rows="1" @input="$emit('update:modelValue', $event.target.value)"
      @keydown="onKeydown" @paste="pasteFiles"></textarea>
    <div class="composer-toolbar">
      <button type="button" class="composer-add" :disabled="uploadDisabled || uploading"
        @click="picker?.click()" :title="$t('launch.composer_add')">
        <span aria-hidden="true" class="add-symbol">+</span><span>{{ $t('launch.composer_add') }}</span>
      </button>
      <input ref="picker" type="file" multiple class="composer-picker" @change="selectFiles" />
      <span :id="hintId" class="composer-hint" role="status" aria-live="polite">{{ hint }}</span>
      <button type="button" class="composer-submit" :disabled="submitDisabled" :title="hint || submitLabel"
        :aria-label="submitLabel" @click="$emit('submit')">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M12 19V5M5 12l7-7 7 7" />
        </svg><span>{{ submitLabel }}</span>
      </button>
    </div>
    <div v-if="dragActive" class="composer-drop-target" aria-hidden="true">{{ $t('launch.drop_files') }}</div>
  </section>
</template>

<script setup>
import { ref, useId } from 'vue'
import vAutosizeTextarea from '../utils/autosizeTextarea'

const props = defineProps({ modelValue: { type: String, default: '' }, attachments: { type: Array, default: () => [] },
  disabled: Boolean, uploadDisabled: Boolean, uploading: Boolean, submitDisabled: Boolean,
  submitLabel: String, hint: String, highlight: Boolean })
const emit = defineEmits(['update:modelValue', 'files', 'retry', 'remove', 'preview', 'submit'])
const input = ref(null)
const picker = ref(null)
const hintId = `composer-hint-${useId()}`
const dragActive = ref(false)
let dragDepth = 0
const isFileDrag = (event) => Array.from(event.dataTransfer?.types || []).includes('Files')
const canUpload = () => !props.uploadDisabled && !props.uploading
const fileSize = (size) => !Number.isFinite(size) ? '—' : size >= 1024*1024 ? `${(size/1024/1024).toFixed(1)} MB` : `${Math.max(1, Math.ceil(size/1024))} KB`
const fileType = (item) => item.name?.includes('.') ? item.name.split('.').pop().toUpperCase().slice(0, 8) : 'FILE'
const selectFiles = (event) => {
  const files = Array.from(event.target.files || [])
  event.target.value = ''
  if (canUpload() && files.length) emit('files', files)
}
const pasteFiles = (event) => {
  const files = Array.from(event.clipboardData?.files || [])
  if (files.length && canUpload()) { event.preventDefault(); emit('files', files) }
}
const dragEnter = (event) => {
  if (!isFileDrag(event)) return
  event.preventDefault()
  if (canUpload()) { dragDepth += 1; dragActive.value = true }
}
const dragOver = (event) => {
  if (!isFileDrag(event)) return
  event.preventDefault()
  event.dataTransfer.dropEffect = canUpload() ? 'copy' : 'none'
}
const dragLeave = (event) => {
  if (!isFileDrag(event)) return
  dragDepth = Math.max(0, dragDepth - 1)
  if (!dragDepth) dragActive.value = false
}
const dropFiles = (event) => {
  if (!isFileDrag(event)) return
  event.preventDefault(); dragDepth = 0; dragActive.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  if (canUpload() && files.length) emit('files', files)
}
const onKeydown = (event) => {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey) && !event.isComposing) {
    event.preventDefault()
    if (!props.submitDisabled) emit('submit')
  }
}
defineExpose({ focus: () => input.value?.focus() })
</script>

<style scoped>
.campaign-composer { position: relative; display: flex; flex-direction: column; container-type: inline-size; min-width: 0; max-height: min(45dvh, 440px); overflow: hidden; border: 1px solid rgba(255,255,255,.18); border-radius: 22px; background: #292e30; box-shadow: 0 6px 24px rgba(0,0,0,.12); transition: border-color .2s, box-shadow .2s; }
.campaign-composer:focus-within, .campaign-composer.is-highlighted { border-color: #a3dbe5; box-shadow: 0 0 0 2px rgba(153,234,249,.08); }
.campaign-composer.is-dragging { border-color: #99eaf9; }
.composer-files { display: flex; flex: 0 0 auto; gap: 10px; overflow-x: auto; padding: 14px 14px 4px; scrollbar-width: thin; scrollbar-color: #657478 transparent; }
.composer-file { position: relative; display: flex; align-items: center; gap: 10px; flex: 0 0 226px; min-width: 0; box-sizing: border-box; min-height: 80px; padding: 10px 26px 10px 10px; border: 1px solid #4b565a; border-radius: 12px; background: #343c40; }
.composer-file.has-error { border-color: #dc8e85; background: #403333; }
.file-preview, .file-symbol { flex: 0 0 44px; height: 52px; display: grid; place-items: center; border: 0; border-radius: 7px; overflow: hidden; background: #25343c; color: #9ddcf1; padding: 0; }
.file-preview { cursor: pointer; }
.file-preview img { width: 100%; height: 100%; object-fit: cover; }
.file-details { display: flex; flex-direction: column; min-width: 0; gap: 4px; }
.file-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #f0f4f4; font-size: 12px; font-weight: 600; }
.file-meta, .file-state { font-size: 10px; color: #b9c8cc; }
.file-state { display: flex; align-items: center; gap: 5px; }
.has-error .file-state { color: #ffb9ae; }
.file-error-detail { color: #ffc4ba; font-size: 10px; max-width: 135px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-remove { position: absolute; right: 5px; top: 5px; width: 24px; height: 24px; border: 0; border-radius: 6px; background: transparent; color: #c7d6da; font-size: 21px; cursor: pointer; }
.file-remove:hover { background: #ffffff16; }
.file-retry { align-self: flex-start; padding: 0; border: 0; background: transparent; color: #bce9fa; text-decoration: underline; font-size: 11px; cursor: pointer; }
.composer-textarea { display: block; box-sizing: border-box; width: 100%; min-width: 0; min-height: 48px; max-height: 30dvh; flex: 1 1 auto; margin: 0; padding: 16px 18px 10px; resize: none; border: 0; background: transparent; color: #f0f3f4; font: 14px/1.65 Inter, sans-serif; outline: none; overflow-y: auto; scrollbar-width: thin; scrollbar-color: #788489 transparent; }
.composer-textarea::placeholder { color: #a0adb2; }
.composer-textarea:disabled { opacity: .65; }
.composer-toolbar { display: flex; flex: 0 0 auto; align-items: center; gap: 12px; padding: 10px 12px 12px; }
.composer-add { display: flex; align-items: center; gap: 7px; padding: 7px 10px; flex: 0 0 auto; border: 0; border-radius: 12px; background: transparent; color: #d5e0e3; font-size: 12px; cursor: pointer; }
.composer-add:hover:not(:disabled) { background: #ffffff0c; }
.add-symbol { font-size: 26px; line-height: 24px; font-weight: 300; }
.composer-picker { display: none; }
.composer-hint { flex: 1; min-width: 0; font-size: 11px; line-height: 1.4; color: #b1bec4; }
.composer-submit { display: flex; align-items: center; justify-content: center; gap: 7px; flex: 0 0 auto; min-height: 40px; border: 0; border-radius: 13px; padding: 0 13px; background: linear-gradient(120deg,#aaffcd,#99d4ff); color: #142d36; font-weight: 650; cursor: pointer; }
button:disabled { opacity: .45; cursor: not-allowed; }
button:focus-visible { outline: 2px solid #a4e2f5; outline-offset: 2px; }
.composer-drop-target { pointer-events: none; position: absolute; inset: 5px; border: 1px dashed #a5e4ec; border-radius: 17px; background: #203c43ed; display: grid; place-items: center; color: #d5f9ff; font-size: 14px; }
.upload-spinner { width: 9px; height: 9px; border: 1.5px solid #86bfc666; border-top-color: #abf2f0; border-radius: 50%; animation: spin .8s linear infinite; }
.campaign-composer.is-empty { display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; align-items: center; min-height: 60px; border-radius: 20px; }
.is-empty .composer-textarea { grid-column: 2; grid-row: 1; padding: 16px 4px; min-height: 56px; height: 56px !important; overflow-y: hidden; }
.is-empty .composer-toolbar { display: contents; }
.is-empty .composer-add { grid-column: 1; grid-row: 1; padding: 6px; justify-content: center; }
.is-empty .composer-add span:last-child, .is-empty .composer-hint, .is-empty .composer-submit span { display: none; }
.is-empty .composer-submit { grid-column: 3; grid-row: 1; margin: 8px; padding: 0 10px; min-height: 36px; }
.campaign-composer.is-locked-empty { display: block; min-height: 48px; }
.is-locked-empty .composer-textarea, .is-locked-empty .composer-add, .is-locked-empty .composer-submit { display: none; }
.is-locked-empty .composer-hint { display: block; padding: 12px 16px; }
@keyframes spin { to { transform: rotate(360deg); } }
@container (max-width: 540px) { .composer-add span:last-child { display: none; } .composer-toolbar { gap: 8px; } .composer-submit { padding: 0 10px; } }
@media (max-height: 600px) { .composer-file { min-height: 68px; } .file-preview, .file-symbol { height: 40px; } .composer-files { padding-top: 8px; } .composer-toolbar { padding-top: 5px; padding-bottom: 7px; } }
@media (prefers-reduced-motion: reduce) { .upload-spinner { animation: none; } .campaign-composer { transition: none; } }
</style>
