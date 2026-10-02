import asyncio

import bcrypt
from starlette.concurrency import run_in_threadpool

from app.core.database import AsyncSessionLocal
from app.models import Board, BoardColumn, Task, User, UserBoardRole

BOARDS = 50
COLUMNS_PER_BOARD = 5
TASKS_PER_COLUMN = 100


async def seed():
    async with AsyncSessionLocal() as db:
        user = User(   # insert user directly into DB to avoid testing register functionality in this test
            email="dummy_email_for_seeding",
            username="user_for_seeding",
            hashed_password=(await run_in_threadpool(
                bcrypt.hashpw,
                "dummy_password_for_seeding".encode(),
                bcrypt.gensalt()
            )).decode()
        )
        db.add(user)
        await db.flush()    # to send in-memory pending changes to get executed on database but in the transaction without commit

        for b in range(BOARDS):
            board = Board(title=f"Benchmark Board {b}")
            db.add(board)
            await db.flush()

            user_board_role = UserBoardRole(user_id=user.id, board_id=board.id, role="owner")
            db.add(user_board_role)

            for c in range(COLUMNS_PER_BOARD):
                column = BoardColumn(
                    board_id=board.id,
                    title=f"Column {c}",
                    index=c
                )
                db.add(column)
                await db.flush()

                for t in range(TASKS_PER_COLUMN):
                    db.add(Task(
                        column_id=column.id,
                        title=f"Task {t}",
                        description="this is a task for benchmarking",
                        index=float(t + 1),
                        version=1
                    ))

        await db.commit()

        print(f"Seeded {BOARDS} boards")


asyncio.run(seed())