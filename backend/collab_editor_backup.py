from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

app = FastAPI(title="Collaborative Text Editor API", version="1.0.0")

# Mock storage
documents: Dict[int, Dict[str, Any]] = {}
doc_counter = 1
op_counter = {"global": 0}

class TextDelta(BaseModel):
    op_id: int
    content: str
    cursor: Optional[int] = None
    user_id: str = "user"

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, doc_id: int):
        await websocket.accept()
        if doc_id not in self.active_connections:
            self.active_connections[doc_id] = []
        self.active_connections[doc_id].append(websocket)

    def disconnect(self, websocket: WebSocket, doc_id: int):
        self.active_connections[doc_id].remove(websocket)

    async def broadcast(self, doc_id: int, message: str):
        disconnected = []
        for connection in self.active_connections.get(doc_id, []):
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        for conn in disconnected:
            self.active_connections[doc_id].remove(conn)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Collaborative Text Editor API - http://127.0.0.1:8000/docs"}

@app.post("/documents/")
async def create_document(title: str = "Untitled Document"):
    global doc_counter
    doc_id = doc_counter
    doc_counter += 1
    documents[doc_id] = {
        "id": doc_id,
        "title": title,
        "content": "",
        "ops": [],
        "created_at": datetime.now().isoformat()
    }
    return documents[doc_id]

@app.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    if doc_id not in documents:
        from fastapi import HTTPException
        raise HTTPException(404, "Document not found")
    return documents[doc_id]

@app.get("/documents/{doc_id}/content")
async def get_content(doc_id: int):
    if doc_id not in documents:
        from fastapi import HTTPException
        raise HTTPException(404, "Document not found")
    return {"content": documents[doc_id]["content"]}

@app.post("/documents/{doc_id}/delta")
async def apply_delta(doc_id: int, delta: TextDelta):
    if doc_id not in documents:
        from fastapi import HTTPException
        raise HTTPException(404, "Document not found")
    
    global op_counter
    op_counter["global"] += 1
    delta.op_id = op_counter["global"]
    documents[doc_id]["content"] += delta.content
    documents[doc_id]["ops"].append(delta.dict())
    
    # Broadcast to all connected clients
    message = json.dumps({
        "type": "delta",
        "delta": delta.dict(),
        "content": documents[doc_id]["content"][-100:]  # Last 100 chars for preview
    })
    await manager.broadcast(doc_id, message)
    
    return {"status": "applied", "op_id": delta.op_id}

@app.websocket("/ws/{doc_id}")
async def websocket_endpoint(websocket: WebSocket, doc_id: int):
    await manager.connect(websocket, doc_id)
    try:
        # Send current content on connect
        if doc_id in documents:
            await websocket.send_text(json.dumps({
                "type": "init",
                "content": documents[doc_id]["content"]
            }))
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(doc_id, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, doc_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

