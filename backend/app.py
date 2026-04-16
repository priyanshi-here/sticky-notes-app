from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Board, Note, engine, Base
from database import get_db

app = FastAPI(title="Sticky Notes API", version="1.0.0")

# WebSocket manager for boards
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

@app.on_event("startup")\nasync def startup():\n    print("Skipping DB connection - using cloud DB. API endpoints ready.")

@app.get("/")
async def root():
    return {"message": "Sticky Notes API running"}

# Boards
@app.post("/boards/")
async def create_board(db: AsyncSession = Depends(get_db)):
    board = Board(title="New Board")
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board

@app.get("/boards/{board_id}")
async def get_board(board_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Board).where(Board.id == board_id)
    result = await db.execute(stmt)
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(404, "Board not found")
    return board

# Notes
@app.get("/boards/{board_id}/notes/")
async def get_notes(board_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Note).where(Note.board_id == board_id)
    result = await db.execute(stmt)
    notes = result.scalars().all()
    return notes

@app.post("/boards/{board_id}/notes/")
async def create_note(board_id: int, content: str, color: str = "yellow", x: int = 0, y: int = 0, db: AsyncSession = Depends(get_db)):
    note = Note(board_id=board_id, content=content, color=color, x=x, y=y)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    await manager.broadcast(board_id, f"note_created:{note.__dict__}")
    return note

@app.put("/notes/{note_id}")
async def update_note(note_id: int, content: str = None, color: str = None, x: int = None, y: int = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(404, "Note not found")
    if content:
        note.content = content
    if color:
        note.color = color
    if x is not None:
        note.x = x
    if y is not None:
        note.y = y
    await db.commit()
    await db.refresh(note)
    board_id = note.board_id
    await manager.broadcast(board_id, f"note_updated:{note.__dict__}")
    return note

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(404, "Note not found")
    await db.delete(note)
    await db.commit()
    board_id = note.board_id
    await manager.broadcast(board_id, f"note_deleted:{note_id}")
    return {"deleted": note_id}

@app.websocket("/ws/{board_id}")
async def websocket_endpoint(websocket: WebSocket, board_id: int):
    await manager.connect(websocket, board_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(board_id, f"message:{data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, board_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

