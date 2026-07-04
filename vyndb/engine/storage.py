import os
import struct
from engine.page import (
    PAGE_SIZE, PAGE_TYPE_HEADER, PAGE_TYPE_DATA,
    PAGE_TYPE_FREE, MAGIC, VERSION,
    make_page, read_page_header, write_page_header,
    set_checksum, validate_page
)

FILE_HEADER_SIZE = PAGE_SIZE
DB_HEADER_STRUCT = struct.Struct('<5sBIIII')

# File header (fits in page 0):
# 0-4:   magic "VYNDB"
# 5:     version
# 6-9:   page_count
# 10-13: first_free_page (0xFFFFFFFF = none)
# 14-17: catalog_page_id
# 18-21: wal_page_id


class StorageError(Exception):
    pass


class StorageManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self._fh = None
        self._page_count = 0
        self._first_free_page = 0xFFFFFFFF
        self._catalog_page_id = 1
        self._wal_page_id = 0xFFFFFFFF

    def open(self):
        if os.path.exists(self.filepath):
            self._fh = open(self.filepath, 'r+b')
            self._load_file_header()
        else:
            self._fh = open(self.filepath, 'w+b')
            self._init_new_file()

    def close(self):
        if self._fh:
            self._flush_file_header()
            self._fh.close()
            self._fh = None

    def _init_new_file(self):
        header_page = make_page(0, PAGE_TYPE_HEADER)
        packed = DB_HEADER_STRUCT.pack(
            MAGIC,
            VERSION,
            2,
            0xFFFFFFFF,
            1,
            0xFFFFFFFF,
        )
        header_page[:DB_HEADER_STRUCT.size] = packed
        set_checksum(header_page)
        self._fh.write(bytes(header_page))

        catalog_page = make_page(1, PAGE_TYPE_DATA)
        self._fh.write(bytes(catalog_page))
        self._fh.flush()

        self._page_count = 2
        self._first_free_page = 0xFFFFFFFF
        self._catalog_page_id = 1
        self._wal_page_id = 0xFFFFFFFF

    def _load_file_header(self):
        self._fh.seek(0)
        raw = self._fh.read(DB_HEADER_STRUCT.size)
        if len(raw) < DB_HEADER_STRUCT.size:
            raise StorageError("File too small to be a vynDB file")
        unpacked = DB_HEADER_STRUCT.unpack(raw)
        if unpacked[0] != MAGIC:
            raise StorageError(f"Not a vynDB file: bad magic {unpacked[0]}")
        if unpacked[1] != VERSION:
            raise StorageError(f"Unsupported vynDB version: {unpacked[1]}")
        self._page_count       = unpacked[2]
        self._first_free_page  = unpacked[3]
        self._catalog_page_id  = unpacked[4]
        self._wal_page_id      = unpacked[5]

    def _flush_file_header(self):
        packed = DB_HEADER_STRUCT.pack(
            MAGIC,
            VERSION,
            self._page_count,
            self._first_free_page,
            self._catalog_page_id,
            self._wal_page_id,
        )
        self._fh.seek(0)
        self._fh.write(packed)
        self._fh.flush()

    def read_page(self, page_id):
        if page_id >= self._page_count:
            raise StorageError(f"Page {page_id} does not exist")
        self._fh.seek(page_id * PAGE_SIZE)
        raw = self._fh.read(PAGE_SIZE)
        if len(raw) != PAGE_SIZE:
            raise StorageError(f"Short read on page {page_id}")
        data = bytearray(raw)
        validate_page(data)
        return data

    def write_page(self, page_id, data):
        if len(data) != PAGE_SIZE:
            raise StorageError(f"Page data must be {PAGE_SIZE} bytes")
        set_checksum(data)
        self._fh.seek(page_id * PAGE_SIZE)
        self._fh.write(bytes(data))
        self._fh.flush()

    def alloc_page(self, page_type=PAGE_TYPE_DATA):
        if self._first_free_page != 0xFFFFFFFF:
            page_id = self._first_free_page
            data = self.read_page(page_id)
            h = read_page_header(data)
            self._first_free_page = h['next_page_id']
            new_data = make_page(page_id, page_type)
            self.write_page(page_id, new_data)
            self._flush_file_header()
            return page_id, new_data

        page_id = self._page_count
        new_data = make_page(page_id, page_type)
        self._fh.seek(page_id * PAGE_SIZE)
        self._fh.write(bytes(new_data))
        self._fh.flush()
        self._page_count += 1
        self._flush_file_header()
        return page_id, new_data

    def free_page(self, page_id):
        data = make_page(page_id, PAGE_TYPE_FREE)
        h = read_page_header(data)
        h['next_page_id'] = self._first_free_page
        write_page_header(data, h)
        self.write_page(page_id, data)
        self._first_free_page = page_id
        self._flush_file_header()

    def page_count(self):
        return self._page_count

    def catalog_page_id(self):
        return self._catalog_page_id

    def iter_pages(self, page_type=None):
        for pid in range(self._page_count):
            data = self.read_page(pid)
            h = read_page_header(data)
            if page_type is None or h['page_type'] == page_type:
                yield pid, data