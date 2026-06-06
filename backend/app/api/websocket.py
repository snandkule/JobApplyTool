"""WebSocket endpoints for real-time updates."""
import asyncio
import json
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

from backend.app.database.session import SessionLocal
from backend.app.models import Application, ApplicationQueue, DaemonState, PendingQuestion

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time updates.

    Sends periodic updates about:
    - Application statistics
    - Queue status
    - Pending questions
    - Daemon status
    """
    await manager.connect(websocket)

    try:
        # Send initial data
        await send_full_update(websocket)

        # Keep connection alive and send updates
        while True:
            try:
                # Wait for client message or timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)

                # Handle client commands
                if data:
                    message = json.loads(data)
                    await handle_client_message(message, websocket)

            except asyncio.TimeoutError:
                # Timeout reached, send periodic update
                await send_full_update(websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def send_full_update(websocket: WebSocket):
    """Send full update to client."""
    db = SessionLocal()

    try:
        # Get statistics
        total_apps = db.query(Application).count()
        submitted = (
            db.query(Application).filter(Application.status == "submitted").count()
        )
        pending = (
            db.query(Application)
            .filter(Application.status == "pending_questions")
            .count()
        )
        failed = db.query(Application).filter(Application.status == "failed").count()

        # Get queue size
        queue_size = (
            db.query(ApplicationQueue)
            .filter(ApplicationQueue.status == "queued")
            .count()
        )

        # Get pending questions count
        pending_questions = (
            db.query(PendingQuestion)
            .filter(PendingQuestion.status == "pending")
            .count()
        )

        # Get daemon status
        daemon_state = db.query(DaemonState).first()
        daemon_running = daemon_state.is_running if daemon_state else False

        # Prepare update message
        update = {
            "type": "update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "stats": {
                    "total_applications": total_apps,
                    "submitted": submitted,
                    "pending_questions": pending,
                    "failed": failed,
                    "success_rate": round((submitted / total_apps * 100) if total_apps > 0 else 0, 1),
                },
                "queue": {
                    "size": queue_size,
                },
                "questions": {
                    "pending_count": pending_questions,
                },
                "daemon": {
                    "is_running": daemon_running,
                    "applications_today": daemon_state.applications_today if daemon_state else 0,
                },
            },
        }

        await manager.send_personal_message(update, websocket)

    finally:
        db.close()


async def handle_client_message(message: dict, websocket: WebSocket):
    """Handle messages from client."""
    command = message.get("command")

    if command == "ping":
        # Respond to ping
        await manager.send_personal_message(
            {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
            websocket
        )

    elif command == "subscribe":
        # Client wants to subscribe to specific updates
        topics = message.get("topics", [])
        # Store subscription preferences (implement if needed)
        await manager.send_personal_message(
            {"type": "subscribed", "topics": topics},
            websocket
        )

    elif command == "refresh":
        # Client requests immediate refresh
        await send_full_update(websocket)


async def broadcast_application_update(application_id: int, status: str):
    """Broadcast application status update to all clients."""
    message = {
        "type": "application_update",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "application_id": application_id,
            "status": status,
        },
    }
    await manager.broadcast(message)


async def broadcast_question_created(question_id: int, question_text: str):
    """Broadcast new pending question to all clients."""
    message = {
        "type": "question_created",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "question_id": question_id,
            "question_text": question_text,
        },
    }
    await manager.broadcast(message)


async def broadcast_daemon_status(is_running: bool):
    """Broadcast daemon status change to all clients."""
    message = {
        "type": "daemon_status",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "is_running": is_running,
        },
    }
    await manager.broadcast(message)


# Export manager for use in other modules
__all__ = ["router", "manager", "broadcast_application_update", "broadcast_question_created", "broadcast_daemon_status"]
