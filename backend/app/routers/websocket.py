"""
CloudBoard – WebSocket Real-time Collaboration Router (Module 8).
Handles live task updates, status sync, typing indicators, and user presence.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Real-time Collaboration"])


class ConnectionManager:
    """Manages active WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_presence: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, user_id: str = "anonymous", user_name: str = "User"):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_presence[user_id] = {
            "name": user_name,
            "connected_at": time.time(),
            "status": "online"
        }
        logger.info(f"WebSocket client connected: {user_id} ({user_name}). Total connections: {len(self.active_connections)}")
        # Notify connected users of presence update
        await self.broadcast({
            "type": "PRESENCE_UPDATE",
            "users": list(self.user_presence.values()),
            "count": len(self.active_connections)
        })

    def disconnect(self, websocket: WebSocket, user_id: str = "anonymous"):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id in self.user_presence:
            del self.user_presence[user_id]
        logger.info(f"WebSocket client disconnected: {user_id}. Remaining: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending WS message: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query("anon-user"),
    user_name: str = Query("Anonymous Developer")
):
    await manager.connect(websocket, user_id=user_id, user_name=user_name)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                msg_type = payload.get("type", "CHAT")
                
                if msg_type == "PING":
                    await websocket.send_json({"type": "PONG", "timestamp": time.time()})
                elif msg_type in ["TASK_UPDATED", "TASK_CREATED", "TASK_DELETED", "TYPING_INDICATOR"]:
                    # Broadcast event to all connected clients
                    await manager.broadcast({
                        "type": msg_type,
                        "sender": user_name,
                        "sender_id": user_id,
                        "payload": payload.get("payload", {}),
                        "timestamp": time.time()
                    })
                else:
                    await manager.broadcast({
                        "type": "EVENT",
                        "sender": user_name,
                        "data": payload,
                        "timestamp": time.time()
                    })
            except json.JSONDecodeError:
                await websocket.send_json({"type": "ERROR", "message": "Invalid JSON format"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id=user_id)
        await manager.broadcast({
            "type": "PRESENCE_UPDATE",
            "users": list(manager.user_presence.values()),
            "count": len(manager.active_connections)
        })
