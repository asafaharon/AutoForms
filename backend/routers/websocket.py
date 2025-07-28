"""
WebSocket router for real-time notifications
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
from backend.services.websocket_manager import websocket_manager
from backend.deps import get_current_user_websocket


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    room_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time notifications"""
    
    # Authenticate user via token
    try:
        if token:
            # Verify token and get user
            user = await get_current_user_websocket(token)
            if user:
                user_id = user.get("id") or user.get("_id")
        
        if not user_id:
            await websocket.close(code=4001, reason="Authentication required")
            return
    except Exception as e:
        await websocket.close(code=4001, reason=f"Authentication failed: {str(e)}")
        return
    
    # Connect to WebSocket manager
    await websocket_manager.connect(websocket, user_id, room_id)
    
    try:
        while True:
            # Listen for messages from client
            data = await websocket.receive_text()
            
            # Handle client messages
            await handle_client_message(websocket, user_id, data)
            
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, user_id: str, message: str):
    """Handle messages from WebSocket clients"""
    try:
        import json
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "ping":
            # Respond to ping
            await websocket_manager.send_personal_message(websocket, {
                "type": "pong",
                "timestamp": data.get("timestamp")
            })
        
        elif message_type == "subscribe_room":
            # Subscribe to room
            room_id = data.get("room_id")
            if room_id:
                await websocket_manager.subscribe_to_room(websocket, room_id)
                await websocket_manager.send_personal_message(websocket, {
                    "type": "room_subscribed",
                    "room_id": room_id
                })
        
        elif message_type == "unsubscribe_room":
            # Unsubscribe from room
            room_id = data.get("room_id")
            if room_id:
                await websocket_manager.unsubscribe_from_room(websocket, room_id)
                await websocket_manager.send_personal_message(websocket, {
                    "type": "room_unsubscribed",
                    "room_id": room_id
                })
        
        elif message_type == "request_stats":
            # Send connection statistics
            stats = websocket_manager.get_connection_stats()
            await websocket_manager.send_personal_message(websocket, {
                "type": "stats",
                "data": stats
            })
        
        else:
            # Unknown message type
            await websocket_manager.send_personal_message(websocket, {
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            })
            
    except json.JSONDecodeError:
        await websocket_manager.send_personal_message(websocket, {
            "type": "error",
            "message": "Invalid JSON message"
        })
    except Exception as e:
        await websocket_manager.send_personal_message(websocket, {
            "type": "error",
            "message": f"Error processing message: {str(e)}"
        })


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return websocket_manager.get_connection_stats()