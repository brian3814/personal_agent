import { User, Bot } from 'lucide-react'

export const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user'
  
  return (
    <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
      <div className={`message-content ${isUser ? 'user' : 'assistant'}`}>
        <div className={`message-avatar ${isUser ? 'user' : 'assistant'}`}>
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </div>
        
        <div className={`message-text ${isUser ? 'user' : 'assistant'}`}>
          {message.content || (message.role === 'assistant' && '...')}
        </div>
      </div>
    </div>
  )
} 