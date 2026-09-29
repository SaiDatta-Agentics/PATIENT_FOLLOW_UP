from typing import List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: List[dict] = []

    async def connect(self, websocket: WebSocket, user: dict):
        await websocket.accept()
        self.connections.append({"socket": websocket, "user": user})

    def disconnect(self, websocket: WebSocket):
        self.connections = [c for c in self.connections if c["socket"] is not websocket]

    async def broadcast(self, event: dict, patient_id=None, staff_only=False):
        stale = []
        for item in list(self.connections):
            user = item["user"]
            if staff_only and user.get("role") == "PATIENT":
                continue
            if patient_id is not None and user.get("role") == "PATIENT" and user.get("patient_id") != patient_id:
                continue
            try:
                await item["socket"].send_json(event)
            except Exception:
                stale.append(item["socket"])
        for ws in stale:
            self.disconnect(ws)


manager = ConnectionManager()
