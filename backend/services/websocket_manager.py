"""
WebSocket manager for real-time notifications
"""
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum


class NotificationType(Enum):
    """Types of notifications"""
    FORM_GENERATED = "form_generated"
    FORM_UPDATED = "form_updated"
    FORM_SUBMITTED = "form_submitted"
    FORM_DELETED = "form_deleted"
    CHAT_MESSAGE = "chat_message"
    SYSTEM_MESSAGE = "system_message"
    USER_ACTIVITY = "user_activity"
    GENERATION_PROGRESS = "generation_progress"
    ERROR = "error"
    SUCCESS = "success"


class WebSocketManager:
    """Manage WebSocket connections and notifications"""
    
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Store room subscriptions (for form-specific notifications)
        self.room_subscriptions: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, room_id: Optional[str] = None):
        """Accept a WebSocket connection"""
        await websocket.accept()
        
        # Add to user connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "room_id": room_id,
            "connected_at": datetime.now(),
            "last_seen": datetime.now()
        }
        
        # Subscribe to room if provided
        if room_id:
            await self.subscribe_to_room(websocket, room_id)
        
        # Send welcome message
        await self.send_personal_message(websocket, {
            "type": NotificationType.SYSTEM_MESSAGE.value,
            "message": "Connected to AutoForms real-time updates",
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"🔌 WebSocket connected: user={user_id}, room={room_id}")
    
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        metadata = self.connection_metadata.get(websocket)
        if not metadata:
            return
        
        user_id = metadata["user_id"]
        room_id = metadata.get("room_id")
        
        # Remove from user connections
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove from room subscriptions
        if room_id and room_id in self.room_subscriptions:
            if websocket in self.room_subscriptions[room_id]:
                self.room_subscriptions[room_id].remove(websocket)
                if not self.room_subscriptions[room_id]:
                    del self.room_subscriptions[room_id]
        
        # Clean up metadata
        del self.connection_metadata[websocket]
        
        print(f"🔌 WebSocket disconnected: user={user_id}, room={room_id}")
    
    async def subscribe_to_room(self, websocket: WebSocket, room_id: str):
        """Subscribe websocket to a room"""
        if room_id not in self.room_subscriptions:
            self.room_subscriptions[room_id] = []
        
        if websocket not in self.room_subscriptions[room_id]:
            self.room_subscriptions[room_id].append(websocket)
            
            # Update metadata
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["room_id"] = room_id
    
    async def unsubscribe_from_room(self, websocket: WebSocket, room_id: str):
        """Unsubscribe websocket from a room"""
        if room_id in self.room_subscriptions:
            if websocket in self.room_subscriptions[room_id]:
                self.room_subscriptions[room_id].remove(websocket)
                if not self.room_subscriptions[room_id]:
                    del self.room_subscriptions[room_id]
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            await self.disconnect(websocket)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections of a user"""
        if user_id not in self.active_connections:
            return
        
        disconnected_connections = []
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"❌ Error sending to user {user_id}: {e}")
                disconnected_connections.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)
    
    async def send_to_room(self, room_id: str, message: Dict[str, Any]):
        """Send message to all connections in a room"""
        if room_id not in self.room_subscriptions:
            return
        
        disconnected_connections = []
        for websocket in self.room_subscriptions[room_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"❌ Error sending to room {room_id}: {e}")
                disconnected_connections.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Send message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)
    
    async def notify_form_generated(self, user_id: str, form_data: Dict[str, Any]):
        """Notify user about form generation completion"""
        message = {
            "type": NotificationType.FORM_GENERATED.value,
            "data": form_data,
            "message": "Form generated successfully!",
            "timestamp": datetime.now().isoformat()
        }
        await self.send_to_user(user_id, message)
    
    async def notify_form_updated(self, user_id: str, form_id: str, form_data: Dict[str, Any]):
        """Notify user about form update"""
        message = {
            "type": NotificationType.FORM_UPDATED.value,
            "form_id": form_id,
            "data": form_data,
            "message": "Form updated successfully!",
            "timestamp": datetime.now().isoformat()
        }
        await self.send_to_user(user_id, message)
        
        # Also notify room if it exists
        await self.send_to_room(f"form_{form_id}", message)
    
    async def notify_form_submitted(self, form_id: str, submission_data: Dict[str, Any]):
        """Notify form owner about new submission"""
        message = {
            "type": NotificationType.FORM_SUBMITTED.value,
            "form_id": form_id,
            "data": submission_data,
            "message": "New form submission received!",
            "timestamp": datetime.now().isoformat()
        }
        await self.send_to_room(f"form_{form_id}", message)
    
    async def notify_generation_progress(self, user_id: str, progress: Dict[str, Any]):
        """Notify user about generation progress"""
        message = {
            "type": NotificationType.GENERATION_PROGRESS.value,
            "data": progress,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_to_user(user_id, message)
    
    async def notify_chat_message(self, user_id: str, form_id: str, message_data: Dict[str, Any]):
        """Notify about chat message"""
        message = {
            "type": NotificationType.CHAT_MESSAGE.value,
            "form_id": form_id,
            "data": message_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_to_user(user_id, message)
    
    async def notify_error(self, user_id: str, error_message: str, error_type: str = "general"):
        """Notify user about error"""
        message = {
            "type": NotificationType.ERROR.value,
            "error_type": error_type,
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_to_user(user_id, message)
    
    async def notify_success(self, user_id: str, success_message: str, data: Optional[Dict[str, Any]] = None):
        """Notify user about success"""
        message = {
            "type": NotificationType.SUCCESS.value,
            "message": success_message,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        await self.send_to_user(user_id, message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        return {
            "total_connections": total_connections,
            "active_users": len(self.active_connections),
            "active_rooms": len(self.room_subscriptions),
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self.active_connections.items()
            }
        }
    
    async def handle_ping_pong(self):
        """Handle ping/pong to keep connections alive"""
        while True:
            await asyncio.sleep(30)  # Send ping every 30 seconds
            
            disconnected_connections = []
            for websocket in list(self.connection_metadata.keys()):
                try:
                    await websocket.ping()
                    # Update last seen
                    self.connection_metadata[websocket]["last_seen"] = datetime.now()
                except Exception:
                    disconnected_connections.append(websocket)
            
            # Clean up disconnected connections
            for websocket in disconnected_connections:
                await self.disconnect(websocket)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# Start ping/pong handler
async def start_websocket_manager():
    """Start the WebSocket manager background tasks"""
    asyncio.create_task(websocket_manager.handle_ping_pong())