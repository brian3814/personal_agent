import { Trash2, Settings } from 'lucide-react'
import { useChatStore } from '@/store/chatStore'

export const ChatHeader = () => {
  const { clearMessages } = useChatStore()

  return (
    <header className="chat-header">
      <div className="header-content">
        <div className="header-left">
          <div className="header-avatar">
            <span>PA</span>
          </div>
          <div>
            <h1 className="header-title">Personal Agent</h1>
            <p className="header-subtitle">AI Assistant with MCP Protocol</p>
          </div>
        </div>
        
        <div className="header-actions">
          <button
            onClick={clearMessages}
            className="header-button"
          >
            <Trash2 size={16} />
          </button>
          <button className="header-button">
            <Settings size={16} />
          </button>
        </div>
      </div>
    </header>
  )
} 