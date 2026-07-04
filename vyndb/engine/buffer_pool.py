from collections import OrderedDict
from engine.page import PAGE_SIZE, set_checksum

DEFAULT_POOL_SIZE = 256


class Frame:
    def __init__(self, page_id, data):
        self.page_id = page_id
        self.data = bytearray(data)
        self.dirty = False
        self.pin_count = 0


class BufferPool:
    def __init__(self, storage, pool_size=DEFAULT_POOL_SIZE):
        self._storage = storage
        self._pool_size = pool_size
        self._frames = OrderedDict()

    def fetch(self, page_id):
        if page_id in self._frames:
            self._frames.move_to_end(page_id)
            frame = self._frames[page_id]
            frame.pin_count += 1
            return frame

        if len(self._frames) >= self._pool_size:
            self._evict()

        data = self._storage.read_page(page_id)
        frame = Frame(page_id, data)
        frame.pin_count = 1
        self._frames[page_id] = frame
        self._frames.move_to_end(page_id)
        return frame

    def unpin(self, page_id, dirty=False):
        if page_id not in self._frames:
            return
        frame = self._frames[page_id]
        frame.pin_count = max(0, frame.pin_count - 1)
        if dirty:
            frame.dirty = True

    def flush(self, page_id):
        if page_id not in self._frames:
            return
        frame = self._frames[page_id]
        if frame.dirty:
            set_checksum(frame.data)
            self._storage.write_page(page_id, frame.data)
            frame.dirty = False

    def flush_all(self):
        for page_id in list(self._frames.keys()):
            self.flush(page_id)

    def _evict(self):
        for page_id, frame in self._frames.items():
            if frame.pin_count == 0:
                if frame.dirty:
                    set_checksum(frame.data)
                    self._storage.write_page(page_id, frame.data)
                del self._frames[page_id]
                return
        raise RuntimeError("Buffer pool full — all frames pinned")

    def new_page(self, page_type=1):
        page_id, data = self._storage.alloc_page(page_type)
        frame = Frame(page_id, data)
        frame.dirty = True
        frame.pin_count = 1
        if len(self._frames) >= self._pool_size:
            self._evict()
        self._frames[page_id] = frame
        return page_id, frame

    def invalidate(self, page_id):
        if page_id in self._frames:
            del self._frames[page_id]

    def is_cached(self, page_id):
        return page_id in self._frames