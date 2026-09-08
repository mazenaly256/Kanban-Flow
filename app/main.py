from fastapi import FastAPI
from app.routers import health, auth, users, boards, board_columns, tasks

app = FastAPI()

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(boards.router)
app.include_router(board_columns.router)
app.include_router(tasks.router)