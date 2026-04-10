# Collaborative Sticky Notes Board

This plan outlines the architecture and steps required to build a real-time collaborative sticky notes application using React, FastAPI, WebSockets, and a PostgreSQL-compatible database (YugabyteDB).

## User Review Required

> [!CAUTION]
> The database connection string for PostgreSQL/YugabyteDB Cloud needs to be provided through an environment variable (`DATABASE_URL`). I will use SQLAlchemy with an async PostgreSQL driver (`asyncpg`). Let me know if you already have a connection string ready to test, or if I should use a local SQLite database for development and testing purposes first.

## Proposed Changes

### Database Setup (Backend)
- Create `backend/` directory.
- Add `models.py` with `Board` and `Note` tables.
- Add `database.py` with SQLAlchemy async setup for Postgres (YugabyteDB compatible).

### Backend Application (FastAPI)
- `backend/main.py`: Setup FastAPI app, REST APIs, and WebSocket endpoint.
- Provide endpoints:
  - `POST /board`: Create a board
  - `GET /board/{board_id}`: Fetch notes
  - `POST /note`: Create note
  - `PUT /note/{id}`: Update note
  - `DELETE /note/{id}`: Delete note
- WebSocket endpoint `/ws/{board_id}` for broadcasting node movements, creation, edits, and deletions.

### Frontend Setup (React + Vite)
- Initialize Vite project with React and TailwindCSS in `frontend/`.
- Routes: `/` (Home, create board button) and `/board/:boardId` (the canvas).
- Components:
  - `StickyNote`: displays editable text, colored background, and handles drag-and-drop.
  - `BoardView`: holds the connections and renders notes.
- Tools: `react-draggable` for easy drag functionality, or vanilla pointer events.

## Open Questions

> [!IMPORTANT]
> 1. **WebSockets vs Socket.IO**: FastAPI has native WebSocket support, but Socket.IO provides features like reconnection and rooms built-in. I plan to use FastAPI's built-in WebSockets with a custom ConnectionManager. Do you have a strong preference?
> 2. **Database Testing**: Do you want me to use SQLite for rapid local development/testing, or would you prefer I set up local PostgreSQL (or assume you will provide a YugabyteDB `DATABASE_URL`) right away?
> 3. **Drag and Drop**: I plan to use `react-draggable` for simplicity. Is that acceptable, or would you prefer another library like `framer-motion` for smoother animations?

## Verification Plan

### Manual Verification
- Start FastAPI dev server.
- Start Vite frontend dev server.
- Open two browser windows side-by-side to the same board URL.
- Verify real-time sync by:
  - Creating a note on Window A (should appear on Window B).
  - Dragging a note on Window A (should update location on Window B).
  - Editing text/color on Window A (should update on Window B).
