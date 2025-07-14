"""WebSocket endpoints for real-time communication."""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.responses import HTMLResponse
from typing import Optional

from src.api.dependencies import (
    get_connection_manager,
    get_current_user
)
from src.models.schemas import User

logger = logging.getLogger(__name__)

websocket_router = APIRouter()


@websocket_router.websocket("/alerts")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    connection_manager = Depends(get_connection_manager)
):
    """WebSocket endpoint for real-time alerts.
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token
        connection_manager: WebSocket connection manager
    """
    user_id = None
    
    try:
        # Authenticate user from token
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        # Validate token and get user
        from jose import jwt, JWTError
        from src.config.settings import settings
        
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            user_id = payload.get("sub")
            
            if not user_id:
                await websocket.close(code=1008, reason="Invalid token")
                return
                
        except JWTError:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Handle WebSocket connection
        await connection_manager.handle_websocket(websocket, user_id)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if user_id:
            await connection_manager.disconnect(user_id)


@websocket_router.get("/test", response_class=HTMLResponse)
async def websocket_test_page():
    """Test page for WebSocket connections."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
            }
            #messages {
                border: 1px solid #ccc;
                height: 400px;
                overflow-y: scroll;
                padding: 10px;
                margin: 20px 0;
                background-color: #f5f5f5;
            }
            .message {
                margin: 5px 0;
                padding: 5px;
                border-radius: 3px;
            }
            .sent {
                background-color: #e3f2fd;
                text-align: right;
            }
            .received {
                background-color: #f3e5f5;
            }
            .system {
                background-color: #fff3e0;
                font-style: italic;
            }
            button {
                padding: 10px 20px;
                margin: 5px;
                cursor: pointer;
            }
            input {
                padding: 10px;
                width: 300px;
                margin: 5px;
            }
        </style>
    </head>
    <body>
        <h1>Sports Betting WebSocket Test</h1>
        
        <div>
            <input type="text" id="token" placeholder="Enter JWT token" />
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        
        <div>
            <button onclick="subscribeSport('NFL')">Subscribe NFL</button>
            <button onclick="subscribeSport('NBA')">Subscribe NBA</button>
            <button onclick="sendPing()">Send Ping</button>
        </div>
        
        <div id="messages"></div>
        
        <div id="status">Status: Disconnected</div>
        
        <script>
            let ws = null;
            const messagesDiv = document.getElementById('messages');
            const statusDiv = document.getElementById('status');
            
            function addMessage(message, type = 'received') {
                const msgDiv = document.createElement('div');
                msgDiv.className = `message ${type}`;
                msgDiv.textContent = typeof message === 'object' ? 
                    JSON.stringify(message, null, 2) : message;
                messagesDiv.appendChild(msgDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function updateStatus(status) {
                statusDiv.textContent = `Status: ${status}`;
            }
            
            function connect() {
                if (ws) {
                    ws.close();
                }
                
                const token = document.getElementById('token').value;
                if (!token) {
                    alert('Please enter a JWT token');
                    return;
                }
                
                const wsUrl = `ws://localhost:8000/ws/alerts?token=${encodeURIComponent(token)}`;
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    updateStatus('Connected');
                    addMessage('Connected to WebSocket', 'system');
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    addMessage(data);
                };
                
                ws.onclose = (event) => {
                    updateStatus('Disconnected');
                    addMessage(`Disconnected: ${event.reason || 'Connection closed'}`, 'system');
                    ws = null;
                };
                
                ws.onerror = (error) => {
                    addMessage(`Error: ${error}`, 'system');
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }
            
            function subscribeSport(sport) {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Not connected');
                    return;
                }
                
                const message = {
                    type: 'subscribe',
                    channel_type: 'sport',
                    channel_id: sport
                };
                
                ws.send(JSON.stringify(message));
                addMessage(message, 'sent');
            }
            
            function sendPing() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Not connected');
                    return;
                }
                
                const message = {
                    type: 'ping',
                    timestamp: new Date().toISOString()
                };
                
                ws.send(JSON.stringify(message));
                addMessage(message, 'sent');
            }
        </script>
    </body>
    </html>
    """
    return html