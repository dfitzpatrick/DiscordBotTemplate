import asyncio
import json
from contextvars import ContextVar
from typing import Callable, List, Dict, Any, Type

import yoyo
import pathlib
import asyncpg
import logging
from urllib.parse import urlparse

from bot.exts.postgres.schema import UnknownEntity, PgNotify

log = logging.getLogger(__name__)
ctx_connection = ContextVar("ctx_connection")
ctx_transaction = ContextVar("ctx_transaction")


async def create_db(dsn: str, database_name: str, owner: str):
    conn = await asyncpg.connect(dsn + "/template1")
    try:
        await conn.execute(f"create database {database_name} owner {owner};")
        await conn.close()
    except asyncpg.DuplicateDatabaseError:
        await conn.close()
        log.debug(f"Skipped Database Creation. {database_name} already created.")


class DbProxy:
    """For later expansion"""
    def __init__(self, connection: asyncpg.Connection):
        log.debug(connection)
        self.connection = connection

    def __await__(self):
        return self.connection.__await__()


class Pg:

    @classmethod
    async def create_tables(cls, dsn: str, database_name: str, migrations_path: pathlib.Path, entity_map: Dict[str, Any] = None, uow_cls: Type[DbProxy] = DbProxy):
        dsn_parts = urlparse(dsn)
        owner = dsn_parts.username
        dsn_database = dsn + f"/{database_name}"
        migrations_folder = str(migrations_path)
        await create_db(dsn, database_name, owner)
        migrations = yoyo.read_migrations(migrations_folder)
        backend = yoyo.get_backend(dsn_database)
        log.debug(f"Running migrations on {database_name}")
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))
        backend.connection.close()
        log.debug("Migrations complete")
        pool = await asyncpg.create_pool(dsn_database)
        conn = await asyncpg.connect(dsn_database)
        return cls(pool, conn, entity_map=entity_map, uow_cls=uow_cls)

    def __init__(self, pool: asyncpg.Pool, connection: asyncpg.Connection, entity_map: Dict[str, Any] = None, uow_cls: Type[DbProxy] = DbProxy):
        self.pool = pool
        self._conn = connection
        self.listeners: List[Callable] = []
        self.entity_map = entity_map or {}
        self._uow_cls = uow_cls

    async def start_listening(self):
        if not self._conn.is_closed():
            await self._conn.add_listener('events', self._notify)

    async def stop_listening(self):
        if self._conn is not None and not self._conn.is_closed():
            await self._conn.remove_listener('events', self._notify)
            await self._conn.close()

    def register_listener(self, callback: Callable):
        self.listeners.append(callback)

    def _notify(self, connection: asyncpg.Connection, pid: int, channel: str, payload: str):
        log.debug(f"PG Notify: {payload}")
        payload = json.loads(payload)

        entity_t = self.entity_map.get(payload['table'])
        if entity_t is None:
            raise UnknownEntity("Did you set an entity map?")
        result = PgNotify(
            table=payload['table'],
            action=payload['action'],
            entity=entity_t(**payload['data'])
        )
        for callback in self.listeners:
            asyncio.create_task(callback(result))

    async def __aenter__(self) -> DbProxy:
        self._conn = await self.pool.acquire()
        self._trans = self._conn.transaction()
        await self._trans.start()
        ctx_connection.set(self._conn)
        ctx_transaction.set(self._trans)
        return self._uow_cls(self._conn)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        conn = ctx_connection.get()
        trans = ctx_transaction.get()
        if exc_type:
            await trans.rollback()
        else:
            await trans.commit()
        try:
            await conn.close()
        except:
            pass