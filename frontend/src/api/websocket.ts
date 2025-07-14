export type MessageHandler = (data: any) => void

export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private messageHandlers = new Set<MessageHandler>()
  
  connect(token: string) {
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/alerts?token=${token}`
    
    this.ws = new WebSocket(wsUrl)
    
    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.messageHandlers.forEach(handler => handler(data))
    }
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.reconnect(token)
    }
  }
  
  private reconnect(token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++
        this.connect(token)
      }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts))
    }
  }
  
  subscribe(topic: string, channelId: string) {
    this.send({
      type: 'subscribe',
      channel_type: topic,
      channel_id: channelId,
    })
  }
  
  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
  
  addMessageHandler(handler: MessageHandler) {
    this.messageHandlers.add(handler)
  }
  
  removeMessageHandler(handler: MessageHandler) {
    this.messageHandlers.delete(handler)
  }
  
  disconnect() {
    this.ws?.close()
  }
}

export const wsService = new WebSocketService()