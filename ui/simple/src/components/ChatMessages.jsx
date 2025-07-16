import { useEffect, useRef } from 'react'
import { MessageBubble } from './MessageBubble'
import { useChatStore } from '@/store/chatStore'

export const ChatMessages = () => {
  const { messages } = useChatStore()
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div className="messages-container" ref={scrollRef}>
      <div className="messages-content">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <div className="welcome-title">Welcome to Personal Agent</div>
            <div className="welcome-subtitle">Start a conversation by typing a message below</div>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}
      </div>
    </div>
  )
} 