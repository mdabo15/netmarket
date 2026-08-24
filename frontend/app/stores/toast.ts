import { defineStore } from 'pinia'

export type ToastType = 'success' | 'error' | 'info'

interface Toast {
  id: number
  type: ToastType
  message: string
}

/**
 * Global, always-visible feedback for confirmations/errors — fixed at the
 * bottom of the screen regardless of scroll position. Replaces the old
 * pattern of an inline v-alert placed wherever in the page flow, which could
 * end up off-screen (e.g. below the fold on a long form) and go unnoticed.
 */
export const useToastStore = defineStore('toast', () => {
  const queue = ref<Toast[]>([])
  let nextId = 0

  function push(type: ToastType, message: string) {
    queue.value.push({ id: nextId++, type, message })
  }

  function dismiss(id: number) {
    queue.value = queue.value.filter((t) => t.id !== id)
  }

  return {
    queue,
    push,
    dismiss,
    success: (message: string) => push('success', message),
    error: (message: string) => push('error', message),
    info: (message: string) => push('info', message),
  }
})
