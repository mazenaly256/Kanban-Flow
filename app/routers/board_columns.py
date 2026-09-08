from fastapi import APIRouter, Depends


router = APIRouter(prefix="/boards/{board_id}/columns", tags=["board columns"])
