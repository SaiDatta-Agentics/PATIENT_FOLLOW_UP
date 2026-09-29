from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.auth import decode_access_token
from app.services.realtime import manager

router = APIRouter(tags=["realtime"])


@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        user = decode_access_token(token)
    except Exception:
        await websocket.close(code=4401)
        return
    await manager.connect(websocket, user)
    try:
        await websocket.send_json({"type": "CONNECTED", "message": "Live updates connected"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
