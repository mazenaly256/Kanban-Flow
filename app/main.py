from fastapi import FastAPI
from app.routers import health, auth, users

app = FastAPI()

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)