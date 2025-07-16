import { ChatHeader } from '@/components/ChatHeader'
import { ChatMessages } from '@/components/ChatMessages'
import { ChatInput } from '@/components/ChatInput'
import { useChat } from '@/hooks/useChat'

function App() {
  const { sendMessage, isLoading } = useChat()

  return (
    <div className="app-container">
      <ChatHeader />
      <ChatMessages />
      <div className="input-container">
        <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
      </div>
    </div>
  )
}

export default App
