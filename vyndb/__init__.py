from engine.storage import StorageManager
from engine.buffer_pool import BufferPool
from engine.page import PAGE_SIZE
from engine.btree import BTree, RID


def open_db(filepath):
    storage = StorageManager(filepath)
    storage.open()
    pool = BufferPool(storage)
    return storage, pool


def close_db(storage, pool):
    pool.flush_all()
    storage.close()