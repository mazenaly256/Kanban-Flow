from fastapi import FastAPI
from app.routers import health, auth

app = FastAPI()

app.include_router(health.router)
app.include_router(auth.router)