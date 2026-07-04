import struct
from engine.page import (
    PAGE_SIZE, PAGE_TYPE_DATA,
    PAGE_HEADER_SIZE, read_page_header,
    write_page_header, make_page, set_checksum
)
from catalog.schema import TableDef, ColumnDef, IndexDef

CATALOG_MAGIC   = b'VCAT'
CATALOG_VERSION = 1

# Catalog is stored as a chain of pages starting at page 1.
# Layout of the byte stream across those pages:
#   4 bytes: magic "VCAT"
#   1 byte:  version
#   4 bytes: table_count
#   [packed TableDef] * table_count
#
# Each page stores:
#   [PAGE_HEADER_SIZE .. PAGE_SIZE-4]: payload bytes
#   last 4 bytes of page: next_page_id (0xFFFFFFFF = end)

NEXT_PTR_SIZE   = 4
PAYLOAD_PER_PAGE = PAGE_SIZE - PAGE_HEADER_SIZE - NEXT_PTR_SIZE


class CatalogError(Exception):
    pass


class Catalog:
    def __init__(self, storage, pool, first_page_id=1):
        self._storage       = storage
        self._pool          = pool
        self._first_page_id = first_page_id
        self._tables        = {}

    def load(self):
        raw = self._read_all_bytes()
        if not raw:
            self._tables = {}
            return
        if raw[:4] != CATALOG_MAGIC:
            raise CatalogError("Invalid catalog magic bytes")
        version = raw[4]
        if version != CATALOG_VERSION:
            raise CatalogError(f"Unsupported catalog version {version}")
        table_count, = struct.unpack_from('<I', raw, 5)
        offset = 9
        self._tables = {}
        for _ in range(table_count):
            table, offset = TableDef.unpack(raw, offset)
            self._tables[table.name] = table

    def save(self):
        payload = self._serialize()
        self._write_all_bytes(payload)

    def _serialize(self):
        parts = [
            CATALOG_MAGIC,
            bytes([CATALOG_VERSION]),
            struct.pack('<I', len(self._tables)),
        ]
        for table in self._tables.values():
            parts.append(table.pack())
        return b''.join(parts)

    def _read_all_bytes(self):
        chunks = []
        page_id = self._first_page_id
        while page_id != 0xFFFFFFFF:
            frame = self._pool.fetch(page_id)
            data = frame.data
            payload_start = PAGE_HEADER_SIZE
            payload_end   = PAGE_SIZE - NEXT_PTR_SIZE
            chunk = bytes(data[payload_start:payload_end])
            next_id, = struct.unpack_from('<I', data, PAGE_SIZE - NEXT_PTR_SIZE)
            self._pool.unpin(page_id)
            chunks.append(chunk)
            page_id = next_id if next_id != 0xFFFFFFFF else None
            if page_id is None:
                break
        if not chunks:
            return b''
        raw = b''.join(chunks)
        # trim trailing zero padding
        return raw.rstrip(b'\x00') if raw else b''

    def _write_all_bytes(self, payload):
        chunks = []
        for i in range(0, max(1, len(payload)), PAYLOAD_PER_PAGE):
            chunks.append(payload[i:i + PAYLOAD_PER_PAGE])

        existing_pages = self._collect_chain()
        needed = len(chunks)

        while len(existing_pages) < needed:
            pid, frame = self._pool.new_page(PAGE_TYPE_DATA)
            self._pool.unpin(pid, dirty=True)
            existing_pages.append(pid)

        for i, (chunk, pid) in enumerate(zip(chunks, existing_pages)):
            frame = self._pool.fetch(pid)
            padded = chunk.ljust(PAYLOAD_PER_PAGE, b'\x00')
            frame.data[PAGE_HEADER_SIZE:PAGE_SIZE - NEXT_PTR_SIZE] = padded

            next_pid = existing_pages[i + 1] if i + 1 < needed else 0xFFFFFFFF
            struct.pack_into('<I', frame.data, PAGE_SIZE - NEXT_PTR_SIZE, next_pid)

            h = read_page_header(frame.data)
            h['next_page_id'] = next_pid
            write_page_header(frame.data, h)
            set_checksum(frame.data)
            self._pool.unpin(pid, dirty=True)
            self._pool.flush(pid)

        for pid in existing_pages[needed:]:
            self._storage.free_page(pid)

    def _collect_chain(self):
        pages = []
        page_id = self._first_page_id
        while page_id != 0xFFFFFFFF:
            pages.append(page_id)
            frame = self._pool.fetch(page_id)
            next_id, = struct.unpack_from('<I', frame.data, PAGE_SIZE - NEXT_PTR_SIZE)
            self._pool.unpin(page_id)
            page_id = next_id if next_id != 0xFFFFFFFF else None
            if page_id is None:
                break
        return pages

    def tables(self):
        return dict(self._tables)

    def get_table(self, name):
        return self._tables.get(name)

    def has_table(self, name):
        return name in self._tables

    def create_table(self, table_def):
        if self.has_table(table_def.name):
            raise CatalogError(f"Table '{table_def.name}' already exists")
        self._tables[table_def.name] = table_def
        self.save()

    def drop_table(self, name):
        if not self.has_table(name):
            raise CatalogError(f"Table '{name}' does not exist")
        del self._tables[name]
        self.save()

    def rename_table(self, old_name, new_name):
        if not self.has_table(old_name):
            raise CatalogError(f"Table '{old_name}' does not exist")
        if self.has_table(new_name):
            raise CatalogError(f"Table '{new_name}' already exists")
        table = self._tables.pop(old_name)
        table.name = new_name
        self._tables[new_name] = table
        self.save()

    def add_column(self, table_name, col_def, position=None):
        table = self._get_or_raise(table_name)
        table.add_column(col_def, position)
        self.save()

    def drop_column(self, table_name, col_name):
        table = self._get_or_raise(table_name)
        table.drop_column(col_name)
        self.save()

    def rename_column(self, table_name, old_name, new_name):
        table = self._get_or_raise(table_name)
        table.rename_column(old_name, new_name)
        self.save()

    def modify_column(self, table_name, col_name, **kwargs):
        table = self._get_or_raise(table_name)
        table.modify_column(col_name, **kwargs)
        self.save()

    def add_index(self, table_name, index_def):
        table = self._get_or_raise(table_name)
        if index_def.name in table.indexes:
            raise CatalogError(f"Index '{index_def.name}' already exists on '{table_name}'")
        table.indexes[index_def.name] = index_def
        self.save()

    def drop_index(self, table_name, index_name):
        table = self._get_or_raise(table_name)
        if index_name not in table.indexes:
            raise CatalogError(f"Index '{index_name}' does not exist on '{table_name}'")
        del table.indexes[index_name]
        self.save()

    def update_row_count(self, table_name, delta):
        table = self._get_or_raise(table_name)
        table.row_count = max(0, table.row_count + delta)
        self.save()

    def set_row_count(self, table_name, count):
        table = self._get_or_raise(table_name)
        table.row_count = max(0, count)
        self.save()

    def _get_or_raise(self, name):
        t = self._tables.get(name)
        if t is None:
            raise CatalogError(f"Table '{name}' does not exist")
        return t

    def alter_table(self, table_name, operation, **kwargs):
        op = operation.upper()
        if op == 'ADD COLUMN':
            self.add_column(table_name, kwargs['col_def'], kwargs.get('position'))
        elif op == 'DROP COLUMN':
            self.drop_column(table_name, kwargs['col_name'])
        elif op == 'RENAME COLUMN':
            self.rename_column(table_name, kwargs['old_name'], kwargs['new_name'])
        elif op == 'RENAME TO':
            self.rename_table(table_name, kwargs['new_name'])
        elif op == 'MODIFY COLUMN':
            self.modify_column(table_name, kwargs['col_name'],
                               new_type=kwargs.get('new_type'),
                               nullable=kwargs.get('nullable'),
                               unique=kwargs.get('unique'),
                               default=kwargs.get('default'))
        else:
            raise CatalogError(f"Unknown ALTER TABLE operation '{operation}'")

    def __repr__(self):
        return f"<Catalog tables={list(self._tables.keys())}>"