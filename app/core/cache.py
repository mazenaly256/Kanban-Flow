from fastapi import Request
from redis import RedisError


async def get_cache_client(request: Request):
    return request.app.state.redis      # what is saved inside the lifespan in main.py


async def cache_board_get(redis_client, board_id: int):
    try:
        return await redis_client.get(f"board:{board_id}")

    except RedisError:
        return None


async def cache_board_set(redis_client, board_id: int, value: str):
    try:    # to avoid crashing when there is a problem in Redis
        await redis_client.set(f"board:{board_id}", value, ex=300)
    except RedisError:
        pass



async def cache_board_delete(redis_client, board_id: int):
    await redis_client.delete(f"board:{board_id}")