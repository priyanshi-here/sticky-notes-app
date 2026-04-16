# Undo Text Editor Conversion - Sticky Notes Restore TODO

## Steps (planned)
1. [ ] Backup collab_editor.py and frontend/ dir
2. [ ] Fix & set sticky backend as main (backend/main_fixed.py → backend/main.py)
3. [ ] Create simple vanilla JS frontend/index.html for sticky notes (drag, API/WS)
4. [ ] Update TODO_COLLAB.md to 'Reverted to sticky notes'
5. [ ] Test: backend uvicorn backend.main:app --reload + open frontend/index.html
6. [ ] Complete reversion

Current progress: Fixing backend errors, database.py fixed.

Run test: python -m uvicorn backend.working_app:app --reload (mock DB sticky notes working)
