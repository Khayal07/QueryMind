import { useRef, useEffect, KeyboardEvent } from 'react'

type PromptBarProps = {
  prompt: string
  setPrompt: (value: string) => void
  onSend: () => void
  loading: boolean
  error: string
}

function PromptBar({ prompt, setPrompt, onSend, loading, error }: PromptBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`
  }, [prompt])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      if (!loading && prompt.trim()) onSend()
    }
  }

  return (
    <section className="prompt-bar">
      <div className="prompt-container">
        <div className="prompt-input-row">
          <textarea
            ref={textareaRef}
            id="nl-query"
            className="prompt-textarea"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question like: Show all customers who bought products above $100"
            rows={1}
          />
          <button
            className={`send-btn ${loading ? 'loading' : ''}`}
            onClick={onSend}
            disabled={loading || !prompt.trim()}
            aria-label="Generate SQL"
          >
            {loading ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 2L11 13" />
                <path d="M22 2L15 22L11 13L2 9L22 2Z" />
              </svg>
            )}
          </button>
        </div>
        <div className="prompt-footer">
          <div className="prompt-hint">
            <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to send
          </div>
          <div className={`prompt-status ${error ? 'error' : ''}`}>
            {error ? (
              <>{`⚠ ${error}`}</>
            ) : loading ? (
              <>✨ Generating SQL...</>
            ) : (
              <>Ready</>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

export default PromptBar
