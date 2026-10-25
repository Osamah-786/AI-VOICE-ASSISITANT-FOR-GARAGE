import { useCallback, useEffect, useRef, useState } from 'react'
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useConnectionState,
  useRoomContext,
  useTextStream,
  useVoiceAssistant,
} from '@livekit/components-react'
import { ConnectionState } from 'livekit-client'
import '@livekit/components-styles'
import './App.css'

const TOKEN_API_URL = import.meta.env.VITE_TOKEN_API_URL || 'http://127.0.0.1:5000'
const ROOM_PREFIX = 'garage-room-'

function ConversationStatus() {
  const connectionState = useConnectionState()
  const { state: agentState, agent } = useVoiceAssistant()

  let label = 'Connecting to LiveKit…'
  if (connectionState === ConnectionState.Connected) {
    if (!agent) label = 'Waiting for Garage AI…'
    else if (agentState === 'listening' || agentState === 'idle') label = 'Listening'
    else if (agentState === 'speaking') label = 'Garage AI is speaking'
    else if (agentState === 'thinking') label = 'Garage AI is thinking'
    else label = 'Connected to Garage AI'
  } else if (connectionState === ConnectionState.Disconnected) {
    label = 'Disconnected'
  }

  return <p className="status" role="status">{label}</p>
}

function ConversationPanel() {
  const room = useRoomContext()
  const connectionState = useConnectionState()
  const { textStreams } = useTextStream('lk.transcription')
  const { state: agentState, agent } = useVoiceAssistant()
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState('')
  const [typedMessages, setTypedMessages] = useState([])
  const transcriptRef = useRef(null)
  const shouldAutoScroll = useRef(true)
  const canSend = connectionState === ConnectionState.Connected && draft.trim().length > 0 && !sending

  const voiceMessages = textStreams.map((stream) => {
    const attributes = stream.streamInfo.attributes || {}
    const segmentId = attributes['lk.segment_id'] || stream.streamInfo.id
    const isAgent = stream.participantInfo.identity !== room.localParticipant.identity
    return {
      id: `${isAgent ? 'agent' : 'user'}-${segmentId}`,
      sender: isAgent ? 'agent' : 'user',
      source: 'voice',
      text: stream.text,
      timestamp: stream.streamInfo.timestamp,
      final: attributes['lk.transcription_final'] === 'true',
    }
  })

  const messages = [...typedMessages, ...voiceMessages]
    .filter((message) => message.text.trim().length > 0)
    .sort((a, b) => a.timestamp - b.timestamp)

  useEffect(() => {
    if (shouldAutoScroll.current && transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight
    }
  }, [messages])

  const sendMessage = async (event) => {
    event.preventDefault()
    const text = draft.trim()
    if (!text || !canSend) return

    setSending(true)
    setSendError('')
    try {
      const info = await room.localParticipant.sendText(text, { topic: 'lk.chat' })
      setTypedMessages((current) => [...current, {
        id: info.id,
        sender: 'user',
        source: 'typed',
        text,
        timestamp: info.timestamp,
        final: true,
      }])
      setDraft('')
    } catch {
      setSendError('Message could not be sent. Your draft is still here—please try again.')
    } finally {
      setSending(false)
    }
  }

  return (
    <section className="text-chat" aria-label="Conversation">
      <div
        className="conversation-transcript"
        ref={transcriptRef}
        onScroll={(event) => {
          const element = event.currentTarget
          shouldAutoScroll.current = element.scrollHeight - element.scrollTop - element.clientHeight < 40
        }}
        aria-live="polite"
        aria-relevant="additions text"
        aria-label="Conversation transcript"
      >
        {messages.length === 0 ? (
          <p className="transcript-empty">Your messages and spoken conversation will appear here.</p>
        ) : messages.map((message) => {
          const isAgent = message.sender === 'agent'
          return (
            <article className={`conversation-message ${isAgent ? 'agent-message' : 'user-message'}`} key={message.id}>
              <span className="conversation-message-label">
                {isAgent ? 'Garage AI' : `You · ${message.source === 'typed' ? 'typed' : 'voice'}`}
              </span>
              <p>{message.text}{!message.final && <span className="transcript-progress" aria-label="transcription in progress">…</span>}</p>
            </article>
          )
        })}
        {agent && agentState === 'thinking' && (
          <article className="conversation-message agent-message thinking-message" role="status" aria-label="Garage AI is thinking">
            <span className="conversation-message-label">Garage AI</span>
            <p>Thinking<span className="thinking-dots" aria-hidden="true">…</span></p>
          </article>
        )}
      </div>
      <form className="composer" onSubmit={sendMessage}>
        <label className="sr-only" htmlFor="message-draft">Write a message</label>
        <textarea
          id="message-draft"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              event.currentTarget.form?.requestSubmit()
            }
          }}
          placeholder="Type a message…"
          rows={2}
          maxLength={4000}
          disabled={connectionState !== ConnectionState.Connected || sending}
        />
        <button className="button button-send" type="submit" disabled={!canSend}>
          {sending ? 'Sending…' : 'Send'}
        </button>
      </form>
      {sendError && <p className="error-message composer-error" role="alert">{sendError}</p>}
      <p className="composer-hint">Enter to send · Shift+Enter for a new line</p>
    </section>
  )
}

function App() {
  const [session, setSession] = useState(null)
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState('')

  const connect = useCallback(async () => {
    setConnecting(true)
    setError('')
    try {
      const sessionId = crypto.randomUUID()
      const room = `${ROOM_PREFIX}${sessionId}`
      const participant = `web-${sessionId}`
      const response = await fetch(
        `${TOKEN_API_URL}/api/token?room=${encodeURIComponent(room)}&participant=${encodeURIComponent(participant)}`,
      )
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Could not get a LiveKit token.')
      if (!data.token || !data.url) throw new Error('The backend returned an incomplete LiveKit response.')
      setSession({ token: data.token, serverUrl: data.url })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not connect to the voice service.')
    } finally {
      setConnecting(false)
    }
  }, [])

  const disconnect = useCallback(() => setSession(null), [])

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-mark" aria-hidden="true">G</div>
        <span className="brand-name">GARAGE AI</span>
        <span className={`connection-pill ${session ? 'is-connected' : ''}`}>
          <span className="connection-dot" />{session ? 'In conversation' : 'Ready'}
        </span>
      </header>

      <section className="assistant-card" aria-live="polite">
        <div className="eyebrow">VOICE SERVICE ASSISTANT</div>
        <div className="orb" aria-hidden="true"><span /></div>
        <h1>Your garage, ready to help.</h1>
        <p className="intro">Talk with Garage AI about your vehicle and service needs.</p>

        {session ? (
          <LiveKitRoom
            token={session.token}
            serverUrl={session.serverUrl}
            connect
            audio
            video={false}
            onError={(err) => {
              setError(err.message || 'LiveKit connection failed.')
              setSession(null)
            }}
            onMediaDeviceFailure={() => setError('Microphone access failed. Allow microphone access in your browser and try again.')}
            onDisconnected={disconnect}
          >
            <RoomAudioRenderer />
            <ConversationStatus />
            {error && <p className="error-message" role="alert">{error}</p>}
            <ConversationPanel />
            <button className="button button-end" onClick={disconnect}>End conversation</button>
          </LiveKitRoom>
        ) : (
          <>
            <p className="status">Your microphone will turn on when you start.</p>
            {error && <p className="error-message" role="alert">{error}</p>}
            <button className="button button-start" onClick={connect} disabled={connecting}>
              <span className="mic-icon" aria-hidden="true">●</span>
              {connecting ? 'Connecting…' : 'Start conversation'}
            </button>
          </>
        )}
        <p className="privacy-note">Microphone access is used only for this conversation.</p>
      </section>
      <footer>Automotive service, made conversational.</footer>
    </main>
  )
}

export default App
