import sqlite3

import aiosqlite


class Storage:
    def __init__(self, db_path):
        self.db_path = db_path

    async def setup(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id integer PRIMARY KEY, 
                    title text NOT NULL, 
                    url text NOT NULL, 
                    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            await db.commit()

    async def insert(self, data):
        async with aiosqlite.connect(self.db_path) as db:
            for item in data:
                await db.execute(
                    """
                    INSERT INTO posts (id, title, url)
                    VALUES (?, ?, ?) ON CONFLICT (id)
                    DO NOTHING;
                    """,
                    (item["id"], item["title"], item["url"])
                )
            await db.commit()

    async def load(self, offset, limit, order):
        direction = 'DESC' if order[0] == '-' else 'ASC'
        order = order.lstrip('-')
        async with aiosqlite.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as db:
            cursor = await db.execute(
                f"""
                SELECT * FROM posts ORDER BY {order} {direction} LIMIT {limit} OFFSET {offset}
                """
            )
            data = await cursor.fetchall()
            data = list(map(lambda x: dict(zip([c[0] for c in cursor.description], x)), data))
            return data
