import { useEffect } from 'react'

export type ToastType = 'success' | 'error' | 'info'

export type ToastMessage = {
  id: number
  type: ToastType
  text: string
}

type ToastProps = {
  toasts: ToastMessage[]
  onDismiss: (id: number) => void
}

const ICONS: Record<ToastType, string> = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
}

function Toast({ toasts, onDismiss }: ToastProps) {
  return (
    <div className="toast-container" role="status" aria-live="polite">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

function ToastItem({ toast, onDismiss }: { toast: ToastMessage; onDismiss: (id: number) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(toast.id), 3000)
    return () => clearTimeout(timer)
  }, [toast.id, onDismiss])

  return (
    <div className={`toast toast-${toast.type}`} onClick={() => onDismiss(toast.id)}>
      <span>{ICONS[toast.type]}</span>
      <span>{toast.text}</span>
    </div>
  )
}

export default Toast
