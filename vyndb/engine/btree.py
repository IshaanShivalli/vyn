import struct
from engine.page import (
    PAGE_SIZE, PAGE_TYPE_INDEX,
    PAGE_HEADER_SIZE, read_page_header, write_page_header, set_checksum
)

ORDER = 100

# B-tree node page layout (after the 32-byte page header):
# 1 byte:  is_leaf
# 2 bytes: key_count
# Then keys and pointers packed:
#   Leaf:     [key(8), rid_page(4), rid_slot(2)] * key_count + next_leaf(4)
#   Internal: [ptr(4)] + [key(8), ptr(4)] * key_count

NODE_META_OFFSET = PAGE_HEADER_SIZE
NODE_META_STRUCT = struct.Struct('<BH')
NODE_META_SIZE   = NODE_META_STRUCT.size

LEAF_ENTRY_STRUCT    = struct.Struct('<qIH')
INTERNAL_KEY_STRUCT  = struct.Struct('<q')
INTERNAL_PTR_STRUCT  = struct.Struct('<I')
NEXT_LEAF_STRUCT     = struct.Struct('<I')

LEAF_ENTRY_SIZE   = LEAF_ENTRY_STRUCT.size
INTERNAL_KEY_SIZE = INTERNAL_KEY_STRUCT.size
INTERNAL_PTR_SIZE = INTERNAL_PTR_STRUCT.size


class RID:
    def __init__(self, page_id, slot_idx):
        self.page_id = page_id
        self.slot_idx = slot_idx

    def __repr__(self):
        return f"RID(page={self.page_id}, slot={self.slot_idx})"


def _read_node_meta(data):
    is_leaf, key_count = NODE_META_STRUCT.unpack_from(data, NODE_META_OFFSET)
    return bool(is_leaf), key_count


def _write_node_meta(data, is_leaf, key_count):
    data[NODE_META_OFFSET:NODE_META_OFFSET + NODE_META_SIZE] = NODE_META_STRUCT.pack(
        1 if is_leaf else 0, key_count
    )


def _leaf_entry_offset(idx):
    return NODE_META_OFFSET + NODE_META_SIZE + idx * LEAF_ENTRY_SIZE


def _read_leaf_entries(data, key_count):
    entries = []
    for i in range(key_count):
        off = _leaf_entry_offset(i)
        key, page_id, slot_idx = LEAF_ENTRY_STRUCT.unpack_from(data, off)
        entries.append((key, RID(page_id, slot_idx)))
    return entries


def _write_leaf_entries(data, entries):
    for i, (key, rid) in enumerate(entries):
        off = _leaf_entry_offset(i)
        data[off:off + LEAF_ENTRY_SIZE] = LEAF_ENTRY_STRUCT.pack(
            key, rid.page_id, rid.slot_idx
        )


def _next_leaf_offset(key_count):
    return _leaf_entry_offset(key_count)


def _read_next_leaf(data, key_count):
    off = _next_leaf_offset(key_count)
    val, = NEXT_LEAF_STRUCT.unpack_from(data, off)
    return val if val != 0xFFFFFFFF else None


def _write_next_leaf(data, key_count, next_page_id):
    off = _next_leaf_offset(key_count)
    data[off:off + NEXT_LEAF_STRUCT.size] = NEXT_LEAF_STRUCT.pack(
        next_page_id if next_page_id is not None else 0xFFFFFFFF
    )


def _internal_base_offset():
    return NODE_META_OFFSET + NODE_META_SIZE


def _read_internal_node(data, key_count):
    off = _internal_base_offset()
    ptr0, = INTERNAL_PTR_STRUCT.unpack_from(data, off)
    off += INTERNAL_PTR_SIZE
    keys = []
    ptrs = [ptr0]
    for _ in range(key_count):
        key, = INTERNAL_KEY_STRUCT.unpack_from(data, off)
        off += INTERNAL_KEY_SIZE
        ptr, = INTERNAL_PTR_STRUCT.unpack_from(data, off)
        off += INTERNAL_PTR_SIZE
        keys.append(key)
        ptrs.append(ptr)
    return keys, ptrs


def _write_internal_node(data, keys, ptrs):
    off = _internal_base_offset()
    data[off:off + INTERNAL_PTR_SIZE] = INTERNAL_PTR_STRUCT.pack(ptrs[0])
    off += INTERNAL_PTR_SIZE
    for i, key in enumerate(keys):
        data[off:off + INTERNAL_KEY_SIZE] = INTERNAL_KEY_STRUCT.pack(key)
        off += INTERNAL_KEY_SIZE
        data[off:off + INTERNAL_PTR_SIZE] = INTERNAL_PTR_STRUCT.pack(ptrs[i + 1])
        off += INTERNAL_PTR_SIZE


class BTree:
    def __init__(self, buffer_pool, root_page_id=None):
        self._bp = buffer_pool
        self._root = root_page_id

    def _new_leaf(self):
        page_id, frame = self._bp.new_page(PAGE_TYPE_INDEX)
        _write_node_meta(frame.data, True, 0)
        _write_next_leaf(frame.data, 0, None)
        set_checksum(frame.data)
        self._bp.unpin(page_id, dirty=True)
        return page_id

    def _new_internal(self, keys, ptrs):
        page_id, frame = self._bp.new_page(PAGE_TYPE_INDEX)
        _write_node_meta(frame.data, False, len(keys))
        _write_internal_node(frame.data, keys, ptrs)
        set_checksum(frame.data)
        self._bp.unpin(page_id, dirty=True)
        return page_id

    def init(self):
        self._root = self._new_leaf()
        return self._root

    @property
    def root_page_id(self):
        return self._root

    def _find_leaf(self, key):
        page_id = self._root
        while True:
            frame = self._bp.fetch(page_id)
            is_leaf, key_count = _read_node_meta(frame.data)
            if is_leaf:
                self._bp.unpin(page_id)
                return page_id
            keys, ptrs = _read_internal_node(frame.data, key_count)
            self._bp.unpin(page_id)
            child = ptrs[0]
            for i, k in enumerate(keys):
                if key < k:
                    break
                child = ptrs[i + 1]
            page_id = child

    def search(self, key):
        leaf_id = self._find_leaf(key)
        frame = self._bp.fetch(leaf_id)
        is_leaf, key_count = _read_node_meta(frame.data)
        entries = _read_leaf_entries(frame.data, key_count)
        self._bp.unpin(leaf_id)
        for k, rid in entries:
            if k == key:
                return rid
        return None

    def range_search(self, low, high):
        leaf_id = self._find_leaf(low)
        results = []
        while leaf_id is not None:
            frame = self._bp.fetch(leaf_id)
            is_leaf, key_count = _read_node_meta(frame.data)
            entries = _read_leaf_entries(frame.data, key_count)
            next_id = _read_next_leaf(frame.data, key_count)
            self._bp.unpin(leaf_id)
            done = False
            for k, rid in entries:
                if k > high:
                    done = True
                    break
                if k >= low:
                    results.append((k, rid))
            if done:
                break
            leaf_id = next_id
        return results

    def insert(self, key, rid):
        result = self._insert_recursive(self._root, key, rid)
        if result is not None:
            mid_key, new_page_id = result
            new_root = self._new_internal([mid_key], [self._root, new_page_id])
            self._root = new_root

    def _insert_recursive(self, page_id, key, rid):
        frame = self._bp.fetch(page_id)
        is_leaf, key_count = _read_node_meta(frame.data)

        if is_leaf:
            entries = _read_leaf_entries(frame.data, key_count)
            next_leaf = _read_next_leaf(frame.data, key_count)
            insert_pos = 0
            for i, (k, _) in enumerate(entries):
                if key <= k:
                    break
                insert_pos = i + 1
            entries.insert(insert_pos, (key, rid))

            if len(entries) <= ORDER:
                _write_node_meta(frame.data, True, len(entries))
                _write_leaf_entries(frame.data, entries)
                _write_next_leaf(frame.data, len(entries), next_leaf)
                set_checksum(frame.data)
                self._bp.unpin(page_id, dirty=True)
                return None

            mid = len(entries) // 2
            left_entries = entries[:mid]
            right_entries = entries[mid:]

            _write_node_meta(frame.data, True, len(left_entries))
            _write_leaf_entries(frame.data, left_entries)

            new_page_id, new_frame = self._bp.new_page(PAGE_TYPE_INDEX)
            _write_node_meta(new_frame.data, True, len(right_entries))
            _write_leaf_entries(new_frame.data, right_entries)
            _write_next_leaf(new_frame.data, len(right_entries), next_leaf)
            _write_next_leaf(frame.data, len(left_entries), new_page_id)

            set_checksum(frame.data)
            set_checksum(new_frame.data)
            self._bp.unpin(page_id, dirty=True)
            self._bp.unpin(new_page_id, dirty=True)
            return right_entries[0][0], new_page_id

        keys, ptrs = _read_internal_node(frame.data, key_count)
        self._bp.unpin(page_id)

        child_idx = len(keys)
        for i, k in enumerate(keys):
            if key < k:
                child_idx = i
                break

        result = self._insert_recursive(ptrs[child_idx], key, rid)
        if result is None:
            return None

        mid_key, new_child = result
        frame = self._bp.fetch(page_id)
        keys.insert(child_idx, mid_key)
        ptrs.insert(child_idx + 1, new_child)

        if len(keys) <= ORDER:
            _write_node_meta(frame.data, False, len(keys))
            _write_internal_node(frame.data, keys, ptrs)
            set_checksum(frame.data)
            self._bp.unpin(page_id, dirty=True)
            return None

        mid = len(keys) // 2
        push_up_key = keys[mid]
        left_keys = keys[:mid]
        right_keys = keys[mid + 1:]
        left_ptrs = ptrs[:mid + 1]
        right_ptrs = ptrs[mid + 1:]

        _write_node_meta(frame.data, False, len(left_keys))
        _write_internal_node(frame.data, left_keys, left_ptrs)
        set_checksum(frame.data)
        self._bp.unpin(page_id, dirty=True)

        new_page_id = self._new_internal(right_keys, right_ptrs)
        return push_up_key, new_page_id

    def delete(self, key):
        leaf_id = self._find_leaf(key)
        frame = self._bp.fetch(leaf_id)
        is_leaf, key_count = _read_node_meta(frame.data)
        entries = _read_leaf_entries(frame.data, key_count)
        next_leaf = _read_next_leaf(frame.data, key_count)
        new_entries = [(k, r) for k, r in entries if k != key]
        _write_node_meta(frame.data, True, len(new_entries))
        _write_leaf_entries(frame.data, new_entries)
        _write_next_leaf(frame.data, len(new_entries), next_leaf)
        set_checksum(frame.data)
        self._bp.unpin(leaf_id, dirty=True)
        return len(new_entries) < len(entries)