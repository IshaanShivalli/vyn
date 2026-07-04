import struct

PAGE_SIZE = 4096
MAGIC = b'VYNDB'
VERSION = 1

PAGE_TYPE_HEADER   = 0
PAGE_TYPE_DATA     = 1
PAGE_TYPE_INDEX    = 2
PAGE_TYPE_OVERFLOW = 3
PAGE_TYPE_FREE     = 4

PAGE_HEADER_SIZE = 32

# Page header layout (32 bytes):
# 0-4:   magic (5 bytes)
# 5:     page_type (1 byte)
# 6-9:   page_id (4 bytes)
# 10-13: next_page_id (4 bytes)  — for overflow/chained pages
# 14-17: prev_page_id (4 bytes)
# 18-19: slot_count (2 bytes)    — number of slots used on this page
# 20-21: free_space_offset (2 bytes) — where free space starts
# 22-25: checksum (4 bytes)
# 26-31: reserved (6 bytes)

HEADER_STRUCT = struct.Struct('<5sBIIIHHI6s')


def make_page(page_id, page_type=PAGE_TYPE_DATA):
    data = bytearray(PAGE_SIZE)
    header = HEADER_STRUCT.pack(
        MAGIC,
        page_type,
        page_id,
        0xFFFFFFFF,
        0xFFFFFFFF,
        0,
        PAGE_SIZE,
        0,
        b'\x00' * 6
    )
    data[:PAGE_HEADER_SIZE] = header
    return data


def read_page_header(data):
    raw = HEADER_STRUCT.unpack_from(data, 0)
    return {
        'magic':             raw[0],
        'page_type':         raw[1],
        'page_id':           raw[2],
        'next_page_id':      raw[3],
        'prev_page_id':      raw[4],
        'slot_count':        raw[5],
        'free_space_offset': raw[6],
        'checksum':          raw[7],
    }


def write_page_header(data, header):
    packed = HEADER_STRUCT.pack(
        header['magic'],
        header['page_type'],
        header['page_id'],
        header['next_page_id'],
        header['prev_page_id'],
        header['slot_count'],
        header['free_space_offset'],
        header['checksum'],
        b'\x00' * 6
    )
    data[:PAGE_HEADER_SIZE] = packed


def compute_checksum(data):
    total = 0
    for i in range(PAGE_HEADER_SIZE, PAGE_SIZE):
        total = (total + data[i]) & 0xFFFFFFFF
    return total


def set_checksum(data):
    h = read_page_header(data)
    h['checksum'] = compute_checksum(data)
    write_page_header(data, h)


def verify_checksum(data):
    h = read_page_header(data)
    return h['checksum'] == compute_checksum(data)


def validate_page(data):
    if len(data) != PAGE_SIZE:
        raise ValueError(f"Invalid page size: {len(data)}")
    h = read_page_header(data)
    if h['magic'] != MAGIC:
        raise ValueError(f"Invalid magic bytes: {h['magic']}")
    if not verify_checksum(data):
        raise ValueError(f"Checksum mismatch on page {h['page_id']}")
    return h


# Slot directory — slots grow from PAGE_HEADER_SIZE upward
# Each slot is 4 bytes: offset (2 bytes) + length (2 bytes)
# Row data grows from end of page downward

SLOT_SIZE = 4
SLOT_STRUCT = struct.Struct('<HH')


def _slot_pos(slot_idx):
    return PAGE_HEADER_SIZE + slot_idx * SLOT_SIZE


def free_space(data):
    h = read_page_header(data)
    slot_end = PAGE_HEADER_SIZE + h['slot_count'] * SLOT_SIZE
    return h['free_space_offset'] - slot_end


def insert_slot(data, record):
    h = read_page_header(data)
    rec_len = len(record)
    needed = rec_len + SLOT_SIZE
    if free_space(data) < needed:
        return -1

    slot_idx = h['slot_count']
    new_offset = h['free_space_offset'] - rec_len

    data[new_offset:new_offset + rec_len] = record

    slot_pos = _slot_pos(slot_idx)
    data[slot_pos:slot_pos + SLOT_SIZE] = SLOT_STRUCT.pack(new_offset, rec_len)

    h['slot_count'] += 1
    h['free_space_offset'] = new_offset
    write_page_header(data, h)
    set_checksum(data)
    return slot_idx


def read_slot(data, slot_idx):
    h = read_page_header(data)
    if slot_idx >= h['slot_count']:
        raise IndexError(f"Slot {slot_idx} out of range")
    slot_pos = _slot_pos(slot_idx)
    offset, length = SLOT_STRUCT.unpack_from(data, slot_pos)
    if offset == 0 and length == 0:
        return None
    return bytes(data[offset:offset + length])


def delete_slot(data, slot_idx):
    h = read_page_header(data)
    if slot_idx >= h['slot_count']:
        raise IndexError(f"Slot {slot_idx} out of range")
    slot_pos = _slot_pos(slot_idx)
    data[slot_pos:slot_pos + SLOT_SIZE] = b'\x00\x00\x00\x00'
    set_checksum(data)


def update_slot(data, slot_idx, new_record):
    old = read_slot(data, slot_idx)
    if old is None:
        raise ValueError(f"Slot {slot_idx} is deleted")
    if len(new_record) <= len(old):
        slot_pos = _slot_pos(slot_idx)
        offset, _ = SLOT_STRUCT.unpack_from(data, slot_pos)
        data[offset:offset + len(new_record)] = new_record
        data[slot_pos:slot_pos + SLOT_SIZE] = SLOT_STRUCT.pack(offset, len(new_record))
        set_checksum(data)
        return True
    delete_slot(data, slot_idx)
    new_idx = insert_slot(data, new_record)
    return new_idx


def iter_slots(data):
    h = read_page_header(data)
    for i in range(h['slot_count']):
        rec = read_slot(data, i)
        if rec is not None:
            yield i, rec


def page_is_full(data, min_record_size=1):
    return free_space(data) < min_record_size + SLOT_SIZE