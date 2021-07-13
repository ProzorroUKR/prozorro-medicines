import asyncio
import logging
from contextvars import ContextVar
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from prozorro.medicines.settings import (
    MONGODB_URI, ENGINE_DB_NAME,
    READ_PREFERENCE, WRITE_CONCERN, READ_CONCERN,
    STALE_REGISTRIES_COUNT,
)

logger = logging.getLogger(__name__)

DB = None
session_var = ContextVar('session', default=None)


async def init_mongodb(*_):
    global DB
    logger.info('init mongodb instance')
    loop = asyncio.get_event_loop()
    conn = AsyncIOMotorClient(MONGODB_URI, io_loop=loop)
    DB = conn.get_database(
        ENGINE_DB_NAME,
        read_preference=READ_PREFERENCE,
        write_concern=WRITE_CONCERN,
        read_concern=READ_CONCERN,
    )
    return DB


async def cleanup_db_client(*_):
    global DB
    if DB:
        DB.client.close()
        DB = None


# history methods
def get_registry_collection():
    return DB.medicines


async def get_registry(name):
    registry = await get_registry_collection().find_one(
        {"type": name},
        projection={"_id": 0, "type": 0},
        sort=[("dateModified", DESCENDING)]
    )
    return registry


async def insert_registry(data):
    return await get_registry_collection().insert_one(data)


async def delete_stale_registries(name):
    registries = await get_registry_collection().find(
        {"type": name},
        projection={"_id": 1},
        sort=[("dateModified", DESCENDING)]
    ).skip(STALE_REGISTRIES_COUNT).to_list(None)
    if registries:
        await get_registry_collection().delete_many({"_id": {"$in": [e["_id"] for e in registries]}})
    return registries
