from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json

# Mock DB for demo (cloud DB timeout issue)
mock_boards = {}
note_counter = 1
board_counter = 1

app = FastAPI(title="Sticky Notes API - Working Demo", version="1.0.0")

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, board_id: int):
        await websocket.accept()
        if board_id not in self.active_connections:
            self.active_connections[board_id] = []
        self.active_connections[board_id].append(websocket)

    def disconnect(self, websocket: WebSocket, board_id: int):
        self.active_connections[board_id].remove(websocket)

    async def broadcast(self, board_id: int, message: str):
        for connection in self.active_connections.get(board_id, []):
            await connection.send_text(message)

manager = ConnectionManager()

class NoteCreate(BaseModel):
    content: str
    color: str = "yellow"
    x: int = 0
    y: int = 0

class NoteUpdate(BaseModel):
    content: Optional[str] = None
    color: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None

@app.get("/")
async def root():
    return {"message": "Sticky Notes API - Working! Visit /docs"}

@app.post("/boards/")
async def create_board():
    global board_counter
    board_id = board_counter
    board_counter += 1
    mock_boards[board_id] = {"id": board_id, "title": "New Board", "notes": []}
    return mock_boards[board_id]

@app.get("/boards/{board_id}")
async def get_board(board_id: int):
    if board_id not in mock_boards:
        raise HTTPException(404, "Board not found")
    return mock_boards[board_id]

@app.get("/boards/{board_id}/notes/")
async def get_notes(board_id: int):
    if board_id not in mock_boards:
        raise HTTPException(404, "Board not found")
    return mock_boards[board_id]["notes"]

@app.post("/boards/{board_id}/notes/")
async def create_note(board_id: int, note: NoteCreate):
    global note_counter
    if board_id not in mock_boards:
        raise HTTPException(404, "Board not found")
    note_id = note_counter
    note_counter += 1
    new_note = {"id": note_id, "board_id": board_id, "content": note.content, "color": note.color, "x": note.x, "y": note.y}
    mock_boards[board_id]["notes"].append(new_note)
    await manager.broadcast(board_id, json.dumps({"type": "note_created", "note": new_note}))
    return new_note

@app.put("/notes/{note_id}")
async def update_note(note_id: int, note_update: NoteUpdate):
    for board_id, board in mock_boards.items():
        for i, note in enumerate(board["notes"]):
            if note["id"] == note_id:
                if note_update.content is not None:
                    note["content"] = note_update.content
                if note_update.color is not None:
                    note["color"] = note_update.color
                if note_update.x is not None:
                    note["x"] = note_update.x
                if note_update.y is not None:
                    note["y"] = note_update.y
                await manager.broadcast(board_id, json.dumps({"type": "note_updated", "note": note}))
                return note
    raise HTTPException(404, "Note not found")

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int):
    for board_id, board in mock_boards.items():
        for i, note in enumerate(board["notes"]):
            if note["id"] == note_id:
                deleted_note = board["notes"].pop(i)
                await manager.broadcast(board_id, json.dumps({"type": "note_deleted", "note_id": note_id}))
                return {"deleted": note_id}
    raise HTTPException(404, "Note not found")

@app.websocket("/ws/{board_id}")
async def websocket_endpoint(websocket: WebSocket, board_id: int):
    await manager.connect(websocket, board_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(board_id, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, board_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
