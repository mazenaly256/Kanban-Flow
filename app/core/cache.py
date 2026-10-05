from fastapi import Request


async def get_cache_client(request: Request):
    return request.app.state.redis      # what is saved inside the lifespan in main.py


async def cache_board_get(redis_client, board_id: int):
    return await redis_client.get(f"board:{board_id}")


async def cache_board_set(redis_client, board_id: int, value: str):
    await redis_client.set(f"board:{board_id}", value, ex=300)



async def cache_board_delete(redis_client, board_id: int):
    await redis_client.delete(f"board:{board_id}")