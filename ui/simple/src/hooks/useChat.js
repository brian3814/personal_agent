import { useChatStore } from '@/store/chatStore'

// Configure your API endpoint here
const API_ENDPOINT = 'http://localhost:5050/query'

export const useChat = () => {
  const { addMessage, updateLastMessage, setLoading, isLoading } = useChatStore()

  const sendMessage = async (content) => {
    // Add user message
    addMessage({
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    })

    // Add empty assistant message
    addMessage({
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    })

    setLoading(true)

    try {
      // Create URL with query parameter
      const url = new URL(API_ENDPOINT)
      url.searchParams.append('q', `"${content}"`)
      
      console.log('Making request to:', url)

      // Send GET request to your API endpoint
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        }
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', response.headers)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Handle Server-Sent Events (SSE) streaming response
      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              console.log('Parsed data:', data)
              
              // Handle the actual backend response format
              if (data.role === 'assistant' && data.content) {
                updateLastMessage(data.content)
              }
              // Also handle MCP protocol response types if they exist
              else if (data.type === 'text' || data.type === 'content') {
                updateLastMessage(data.content || data.text || '')
              } else if (data.type === 'tool_call') {
                updateLastMessage(`\n\n**Tool Call:** ${data.tool_name || data.name}\n`)
              } else if (data.type === 'tool_result') {
                updateLastMessage(`**Result:** ${data.content || data.result}\n\n`)
              } else if (data.type === 'error') {
                updateLastMessage(`**Error:** ${data.message}\n`)
              }
            } catch (e) {
              // Skip malformed JSON lines
              console.warn('Failed to parse SSE data:', line, e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      updateLastMessage(`Error: ${error.message || 'Failed to get response'}`)
    } finally {
      setLoading(false)
    }
  }

  return {
    sendMessage,
    isLoading
  }
} 