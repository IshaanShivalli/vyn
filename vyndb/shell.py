import os
import sys
import struct
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from catalog import Catalog, CatalogError, ColumnDef, TableDef, IndexDef
from query import run_query, LexerError, ParseError, ExecutionError
from query.executor import Executor
from engine.storage import StorageManager, StorageError
from engine.buffer_pool import BufferPool
from engine.btree import BTree, RID
from engine.page import (
    PAGE_TYPE_DATA, make_page, read_page_header,
    insert_slot, read_slot, delete_slot, iter_slots, free_space
)

VERSION = "0.1.0"
PROMPT = "vyndb> "
CONTINUATION = "   ... "

_storage = None
_pool = None
_executor = None
_current_db = None
_tables = {}
_indexes = {}
_catalog = None
_history = []


def _print_banner():
    print(f"""
  ██╗   ██╗██╗   ██╗███╗   ██╗██████╗ ██████╗ 
  ██║   ██║╚██╗ ██╔╝████╗  ██║██╔══██╗██╔══██╗
  ██║   ██║ ╚████╔╝ ██╔██╗ ██║██║  ██║██████╔╝
  ╚██╗ ██╔╝  ╚██╔╝  ██║╚██╗██║██║  ██║██╔══██╗
   ╚████╔╝    ██║   ██║ ╚████║██████╔╝██████╔╝
    ╚═══╝     ╚═╝   ╚═╝  ╚═══╝╚═════╝ ╚═════╝ 
  VynDB Shell v{VERSION}
  Type HELP for commands. Type EXIT to quit.
""")

def _ok(msg=""):
    if msg:
        print(f"  \033[32m✓\033[0m  {msg}")


def _err(msg):
    print(f"  \033[31m✗\033[0m  {msg}")


def _info(msg):
    print(f"  \033[34m→\033[0m  {msg}")


def _table(headers, rows):
    if not rows:
        print("  (no rows)")
        return
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    header_row = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    print(f"  {sep}")
    print(f"  {header_row}")
    print(f"  {sep}")
    for row in rows:
        r = "| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)) + " |"
        print(f"  {r}")
    print(f"  {sep}")
    print(f"  {len(rows)} row(s)")


def _pack_row(row_dict, schema):
    parts = []
    for col in schema['columns']:
        val = row_dict.get(col['name'])
        ctype = col['type'].upper()
        if ctype == 'INT':
            if val is None:
                val = 0
            parts.append(struct.pack('<q', int(val)))
        elif ctype == 'FLOAT':
            if val is None:
                val = 0.0
            parts.append(struct.pack('<d', float(val)))
        elif ctype == 'BOOL':
            parts.append(struct.pack('<B', 1 if val else 0))
        else:
            s = str(val) if val is not None else ''
            encoded = s.encode('utf-8')[:255]
            parts.append(struct.pack('<H', len(encoded)) + encoded)
    return b''.join(parts)


def _unpack_row(data, schema):
    row = {}
    offset = 0
    for col in schema['columns']:
        ctype = col['type'].upper()
        if ctype == 'INT':
            val, = struct.unpack_from('<q', data, offset)
            offset += 8
            row[col['name']] = val
        elif ctype == 'FLOAT':
            val, = struct.unpack_from('<d', data, offset)
            offset += 8
            row[col['name']] = val
        elif ctype == 'BOOL':
            val, = struct.unpack_from('<B', data, offset)
            offset += 1
            row[col['name']] = bool(val)
        else:
            length, = struct.unpack_from('<H', data, offset)
            offset += 2
            val = data[offset:offset + length].decode('utf-8')
            offset += length
            row[col['name']] = val
    return row



def cmd_open(args):
    global _storage, _pool, _current_db, _catalog, _executor
    if not args:
        _err("Usage: OPEN <filename>")
        return
    path = args[0]
    if not path.endswith('.vyndb'):
        path += '.vyndb'
    if _storage:
        _catalog.save()
        _pool.flush_all()
        _storage.close()
    try:
        _storage = StorageManager(path)
        _storage.open()
        _pool = BufferPool(_storage)
        _catalog = Catalog(_storage, _pool, first_page_id=1)
        _catalog.load()
        _executor = Executor(_catalog, _pool, _storage)
        _current_db = path
        _ok(f"Opened database: {path}")
        _info(f"Pages: {_storage.page_count()}")
        _info(f"Tables: {len(_catalog.tables())}")
    except Exception as exc:
        _err(f"Failed to open: {exc}")


def cmd_close(args):
    global _storage, _pool, _current_db, _catalog, _executor
    if _storage is None:
        _err("No database open")
        return
    _catalog.save()
    _pool.flush_all()
    _storage.close()
    _storage = None
    _pool = None
    _current_db = None
    _catalog = None
    _ok("Database closed")


def cmd_create_table(args):
    if _storage is None:
        _err("No database open. Use OPEN <file> first.")
        return
    raw = ' '.join(args)
    import re
    m = re.match(r'(\w+)\s*\((.+)\)', raw, re.DOTALL)
    if not m:
        _err("Usage: CREATE TABLE name (col type, col type, ...)")
        return
    name = m.group(1).strip()
    if name in _tables:
        _err(f"Table '{name}' already exists")
        return
    col_defs = m.group(2).strip()
    columns = []
    for part in col_defs.split(','):
        part = part.strip()
        tokens = part.split()
        if len(tokens) < 2:
            _err(f"Bad column definition: '{part}'")
            return
        col_name = tokens[0]
        col_type = tokens[1].upper()
        if col_type not in ('INT', 'FLOAT', 'BOOL', 'TEXT', 'VARCHAR'):
            _err(f"Unknown type '{col_type}'. Supported: INT FLOAT BOOL TEXT VARCHAR")
            return
        pk = 'PRIMARY' in [t.upper() for t in tokens]
        nullable = 'NOT' not in [t.upper() for t in tokens]
        columns.append({'name': col_name, 'type': col_type, 'primary_key': pk, 'nullable': nullable})

    page_id, frame = _pool.new_page(PAGE_TYPE_DATA)
    _pool.unpin(page_id, dirty=True)
    _pool.flush(page_id)

    _tables[name] = {
        'columns': columns,
        'root_page': page_id,
        'row_count': 0
    }
    
    _ok(f"Table '{name}' created (root page: {page_id})")
    col_display = [(c['name'], c['type'], 'PK' if c['primary_key'] else '', 'NOT NULL' if not c['nullable'] else '') for c in columns]
    _table(['Column', 'Type', 'Key', 'Constraint'], col_display)


def cmd_drop_database(args):
    global _storage, _pool, _current_db, _catalog, _executor
    if _storage is None:
        _err("No database open")
        return
    path = _current_db
    _pool.flush_all()
    _storage.close()
    _storage = None
    _pool = None
    _current_db = None
    _catalog = None
    _executor = None
    os.remove(path)
    _ok(f"Database '{path}' deleted")


def _run_sql(sql):
    if _executor is None:
        _err("No database open. Use OPEN <file> first.")
        return
    try:
        rows = run_query(sql, _catalog, _pool, _storage)
        if not rows:
            _info("(no rows returned)")
            return
        first = rows[0]
        if 'status' in first:
            _ok(first['status'])
            return
        if 'inserted' in first:
            _ok(f"{first['inserted']} row(s) inserted")
            return
        if 'updated' in first:
            _ok(f"{first['updated']} row(s) updated")
            return
        if 'deleted' in first:
            _ok(f"{first['deleted']} row(s) deleted")
            return
        if 'plan' in first:
            print(f"\n{first['plan']}\n")
            return
        headers = list(first.keys())
        _table(headers, [[row.get(h, '') for h in headers] for row in rows])
    except (LexerError, ParseError) as exc:
        _err(f"Syntax error: {exc}")
    except ExecutionError as exc:
        _err(f"Execution error: {exc}")
    except Exception as exc:
        _err(f"Error: {exc}")
        if os.environ.get('VYNDB_DEBUG'):
            import traceback
            traceback.print_exc()

def cmd_drop_index(args):
    if _storage is None:
        _err("No database open")
        return
    if not args:
        _err("Usage: DROP INDEX name ON table")
        return
    import re
    raw = ' '.join(args)
    m = re.match(r'(\w+)\s+ON\s+(\w+)', raw, re.IGNORECASE)
    if not m:
        idx_name = args[0]
        for name, schema in _tables.items():
            if idx_name in schema.get('indexes', {}):
                del schema['indexes'][idx_name]
                _ok(f"Index '{idx_name}' dropped")
                return
        _err(f"Index '{idx_name}' not found")
        return
    idx_name = m.group(1)
    table = m.group(2)
    if table not in _tables:
        _err(f"Table '{table}' does not exist")
        return
    if idx_name not in _tables[table].get('indexes', {}):
        _err(f"Index '{idx_name}' does not exist on '{table}'")
        return
    del _tables[table]['indexes'][idx_name]
    _ok(f"Index '{idx_name}' dropped from '{table}'")


def cmd_insert(args):
    if _storage is None:
        _err("No database open")
        return
    raw = ' '.join(args)
    import re
    m = re.match(r'INTO\s+(\w+)\s+VALUES\s*\((.+)\)', raw, re.IGNORECASE | re.DOTALL)
    if not m:
        _err("Usage: INSERT INTO table VALUES (v1, v2, ...)")
        return
    name = m.group(1)
    if name not in _tables:
        _err(f"Table '{name}' does not exist")
        return
    schema = _tables[name]
    raw_vals = m.group(2)
    vals = [v.strip().strip("'\"") for v in raw_vals.split(',')]
    if len(vals) != len(schema['columns']):
        _err(f"Expected {len(schema['columns'])} values, got {len(vals)}")
        return
    row = {}
    for i, col in enumerate(schema['columns']):
        ctype = col['type'].upper()
        v = vals[i]
        try:
            if ctype == 'INT':
                row[col['name']] = int(v)
            elif ctype == 'FLOAT':
                row[col['name']] = float(v)
            elif ctype == 'BOOL':
                row[col['name']] = v.lower() in ('true', '1', 'yes')
            else:
                row[col['name']] = v
        except ValueError:
            _err(f"Cannot convert '{v}' to {ctype} for column '{col['name']}'")
            return

    packed = _pack_row(row, schema)
    page_id = schema['root_page']
    inserted = False
    while True:
        frame = _pool.fetch(page_id)
        h = read_page_header(frame.data)
        if free_space(frame.data) >= len(packed) + 4:
            slot = insert_slot(frame.data, packed)
            if slot == -1:
                _err("Page full and overflow failed")
                return
            _pool.unpin(page_id, dirty=True)
            _pool.flush(page_id)
            inserted = True
            break
        next_pid = h['next_page_id']
        _pool.unpin(page_id)
        if next_pid == 0xFFFFFFFF:
            new_pid, new_frame = _pool.new_page(PAGE_TYPE_DATA)
            frame2 = _pool.fetch(page_id)
            h2 = read_page_header(frame2.data)
            h2['next_page_id'] = new_pid
            from engine.page import write_page_header
            write_page_header(frame2.data, h2)
            _pool.unpin(page_id, dirty=True)
            _pool.flush(page_id)
            slot = insert_slot(new_frame.data, packed)
            _pool.unpin(new_pid, dirty=True)
            _pool.flush(new_pid)
            page_id = new_pid
            inserted = True
            break
        page_id = next_pid

    if inserted:
        schema['row_count'] += 1
        
        _ok(f"1 row inserted into '{name}'")


def _eval_where(row, where_clause):
    if not where_clause:
        return True
    import re
    where_clause = where_clause.strip()
    ops = [('!=', lambda a, b: str(a) != str(b)),
           ('>=', lambda a, b: _cmp(a, b) >= 0),
           ('<=', lambda a, b: _cmp(a, b) <= 0),
           ('=',  lambda a, b: str(a) == str(b)),
           ('>',  lambda a, b: _cmp(a, b) > 0),
           ('<',  lambda a, b: _cmp(a, b) < 0)]
    for op_str, op_fn in ops:
        if op_str in where_clause:
            left, right = where_clause.split(op_str, 1)
            left = left.strip()
            right = right.strip().strip("'\"")
            val = row.get(left)
            if val is None:
                return False
            return op_fn(val, right)
    return True


def _cmp(a, b):
    try:
        return (float(a) > float(b)) - (float(a) < float(b))
    except (ValueError, TypeError):
        return (str(a) > str(b)) - (str(a) < str(b))


def _scan_table(name, where_clause=None, columns=None):
    schema = _tables[name]
    rows = []
    page_id = schema['root_page']
    while page_id != 0xFFFFFFFF:
        frame = _pool.fetch(page_id)
        h = read_page_header(frame.data)
        for slot_idx, rec in iter_slots(frame.data):
            row = _unpack_row(rec, schema)
            if _eval_where(row, where_clause):
                if columns and columns != ['*']:
                    row = {k: v for k, v in row.items() if k in columns}
                rows.append(row)
        next_pid = h['next_page_id']
        _pool.unpin(page_id)
        page_id = next_pid
    return rows


def cmd_select(args):
    if _storage is None:
        _err("No database open")
        return
    import re
    raw = ' '.join(args)
    m = re.match(r'(.+?)\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?(?:\s+ORDER\s+BY\s+(\w+)(\s+DESC)?)?(?:\s+LIMIT\s+(\d+))?(?:\s+OFFSET\s+(\d+))?', raw, re.IGNORECASE)
    if not m:
        _err("Usage: SELECT cols FROM table [WHERE cond] [ORDER BY col [DESC]] [LIMIT n] [OFFSET n]")
        return
    col_part  = m.group(1).strip()
    table     = m.group(2).strip()
    where     = m.group(3)
    order_col = m.group(4)
    order_desc= bool(m.group(5))
    limit     = int(m.group(6)) if m.group(6) else None
    offset    = int(m.group(7)) if m.group(7) else 0

    if table not in _tables:
        _err(f"Table '{table}' does not exist")
        return

    columns = [c.strip() for c in col_part.split(',')] if col_part != '*' else ['*']
    rows = _scan_table(table, where_clause=where, columns=columns)

    if order_col:
        rows.sort(key=lambda r: r.get(order_col, ''), reverse=order_desc)
    if offset:
        rows = rows[offset:]
    if limit is not None:
        rows = rows[:limit]

    if not rows:
        _info("(no rows returned)")
        return

    headers = list(rows[0].keys())
    _table(headers, [[row.get(h, '') for h in headers] for row in rows])


def cmd_update(args):
    if _storage is None:
        _err("No database open")
        return
    import re
    raw = ' '.join(args)
    m = re.match(r'(\w+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$', raw, re.IGNORECASE)
    if not m:
        _err("Usage: UPDATE table SET col=val [WHERE cond]")
        return
    name   = m.group(1)
    set_part = m.group(2)
    where  = m.group(3)
    if name not in _tables:
        _err(f"Table '{name}' does not exist")
        return
    schema = _tables[name]
    updates = {}
    for pair in set_part.split(','):
        k, v = pair.split('=', 1)
        updates[k.strip()] = v.strip().strip("'\"")

    updated = 0
    page_id = schema['root_page']
    while page_id != 0xFFFFFFFF:
        frame = _pool.fetch(page_id)
        h = read_page_header(frame.data)
        dirty = False
        for slot_idx, rec in list(iter_slots(frame.data)):
            row = _unpack_row(rec, schema)
            if _eval_where(row, where):
                for k, v in updates.items():
                    col = next((c for c in schema['columns'] if c['name'] == k), None)
                    if col:
                        ctype = col['type'].upper()
                        if ctype == 'INT':
                            row[k] = int(v)
                        elif ctype == 'FLOAT':
                            row[k] = float(v)
                        elif ctype == 'BOOL':
                            row[k] = v.lower() in ('true', '1', 'yes')
                        else:
                            row[k] = v
                packed = _pack_row(row, schema)
                delete_slot(frame.data, slot_idx)
                insert_slot(frame.data, packed)
                updated += 1
                dirty = True
        next_pid = h['next_page_id']
        _pool.unpin(page_id, dirty=dirty)
        if dirty:
            _pool.flush(page_id)
        page_id = next_pid
    _ok(f"{updated} row(s) updated")


def cmd_delete(args):
    if _storage is None:
        _err("No database open")
        return
    import re
    raw = ' '.join(args)
    m = re.match(r'FROM\s+(\w+)(?:\s+WHERE\s+(.+))?$', raw, re.IGNORECASE)
    if not m:
        _err("Usage: DELETE FROM table [WHERE cond]")
        return
    name  = m.group(1)
    where = m.group(2)
    if name not in _tables:
        _err(f"Table '{name}' does not exist")
        return
    schema = _tables[name]
    deleted = 0
    page_id = schema['root_page']
    while page_id != 0xFFFFFFFF:
        frame = _pool.fetch(page_id)
        h = read_page_header(frame.data)
        dirty = False
        for slot_idx, rec in list(iter_slots(frame.data)):
            row = _unpack_row(rec, schema)
            if _eval_where(row, where):
                delete_slot(frame.data, slot_idx)
                deleted += 1
                dirty = True
        next_pid = h['next_page_id']
        _pool.unpin(page_id, dirty=dirty)
        if dirty:
            _pool.flush(page_id)
        page_id = next_pid
    schema['row_count'] = max(0, schema['row_count'] - deleted)
    
    _ok(f"{deleted} row(s) deleted")


def cmd_create_index(args):
    if _storage is None:
        _err("No database open")
        return
    import re
    raw = ' '.join(args)
    m = re.match(r'(?:INDEX\s+)?(\w+)\s+ON\s+(\w+)\s*\((\w+)\)', raw, re.IGNORECASE)
    if not m:
        _err("Usage: CREATE INDEX name ON table (column)")
        return
    idx_name  = m.group(1)
    table     = m.group(2)
    col_name  = m.group(3)
    if table not in _tables:
        _err(f"Table '{table}' does not exist")
        return
    schema = _tables[table]
    col = next((c for c in schema['columns'] if c['name'] == col_name), None)
    if not col:
        _err(f"Column '{col_name}' does not exist in '{table}'")
        return
    tree = BTree(_pool)
    root = tree.init()
    rows = _scan_table(table)
    for i, row in enumerate(rows):
        val = row.get(col_name)
        if val is not None:
            try:
                key = int(float(str(val)))
                tree.insert(key, RID(schema['root_page'], i))
            except (ValueError, TypeError):
                pass
    if 'indexes' not in schema:
        schema['indexes'] = {}
    schema['indexes'][idx_name] = {'column': col_name, 'root_page': root}
    
    _ok(f"Index '{idx_name}' created on '{table}.{col_name}' (root page: {root})")


def cmd_describe(args):
    if not args:
        _err("Usage: DESCRIBE table")
        return
    name = args[0]
    if _catalog is None:
        _err("No database open")
        return
    t = _catalog.get_table(name)
    if t is None:
        _err(f"Table '{name}' does not exist")
        return
    rows = [(c.name, c.col_type,
             'YES' if c.primary_key else '',
             'NOT NULL' if not c.nullable else 'NULL')
            for c in t.columns]
    print(f"\n  Table: {name}")
    _table(['Column', 'Type', 'Key', 'Null'], rows)
    _info(f"Root page: {t.root_page}")
    _info(f"Row count: {t.row_count}")
    if t.indexes:
        print()
        idx_rows = [(k, v.column_name, v.root_page)
                    for k, v in t.indexes.items()]
        _table(['Index', 'Column', 'Root Page'], idx_rows)



def cmd_tables(args):
    if _catalog is None:
        _err("No database open")
        return
    tables = _catalog.tables()
    if not tables:
        _info("No tables")
        return
    rows = [(name, len(t.columns), t.row_count, t.root_page)
            for name, t in tables.items()]
    _table(['Table', 'Columns', 'Rows', 'Root Page'], rows)




def cmd_pages(args):
    if _storage is None:
        _err("No database open")
        return
    type_names = {0: 'HEADER', 1: 'DATA', 2: 'INDEX', 3: 'OVERFLOW', 4: 'FREE'}
    rows = []
    for pid, data in _storage.iter_pages():
        if pid == 0:
            continue
        h = read_page_header(data)
        rows.append((pid, type_names.get(h['page_type'], '?'),
                     h['slot_count'], free_space(data), h['checksum']))
    _table(['Page ID', 'Type', 'Slots', 'Free Bytes', 'Checksum'], rows)


def cmd_alter_table(args):
    if _storage is None:
        _err("No database open")
        return
    import re
    raw = ' '.join(args)

    m = re.match(r'(\w+)\s+ADD\s+COLUMN\s+(\w+)\s+(\w+)(.*)', raw, re.IGNORECASE)
    if m:
        table_name = m.group(1)
        col_name   = m.group(2)
        col_type   = m.group(3).upper()
        extras     = m.group(4).upper()
        col = ColumnDef(col_name, col_type,
                        nullable='NOT NULL' not in extras,
                        unique='UNIQUE' in extras)
        try:
            _catalog.alter_table(table_name, 'ADD COLUMN', col_def=col)
            _ok(f"Column '{col_name}' added to '{table_name}'")
        except Exception as exc:
            _err(str(exc))
        return

    m = re.match(r'(\w+)\s+DROP\s+COLUMN\s+(\w+)', raw, re.IGNORECASE)
    if m:
        try:
            _catalog.alter_table(m.group(1), 'DROP COLUMN', col_name=m.group(2))
            _ok(f"Column '{m.group(2)}' dropped from '{m.group(1)}'")
        except Exception as exc:
            _err(str(exc))
        return

    m = re.match(r'(\w+)\s+RENAME\s+COLUMN\s+(\w+)\s+TO\s+(\w+)', raw, re.IGNORECASE)
    if m:
        try:
            _catalog.alter_table(m.group(1), 'RENAME COLUMN',
                                 old_name=m.group(2), new_name=m.group(3))
            _ok(f"Column '{m.group(2)}' renamed to '{m.group(3)}'")
        except Exception as exc:
            _err(str(exc))
        return

    m = re.match(r'(\w+)\s+RENAME\s+TO\s+(\w+)', raw, re.IGNORECASE)
    if m:
        try:
            _catalog.alter_table(m.group(1), 'RENAME TO', new_name=m.group(2))
            _ok(f"Table '{m.group(1)}' renamed to '{m.group(2)}'")
        except Exception as exc:
            _err(str(exc))
        return

    m = re.match(r'(\w+)\s+MODIFY\s+COLUMN\s+(\w+)\s+(\w+)(.*)', raw, re.IGNORECASE)
    if m:
        table_name = m.group(1)
        col_name   = m.group(2)
        new_type   = m.group(3).upper()
        extras     = m.group(4).upper()
        try:
            _catalog.alter_table(table_name, 'MODIFY COLUMN',
                                 col_name=col_name,
                                 new_type=new_type,
                                 nullable='NOT NULL' not in extras)
            _ok(f"Column '{col_name}' modified in '{table_name}'")
        except Exception as exc:
            _err(str(exc))
        return

    _err("Usage: ALTER TABLE name ADD/DROP/RENAME/MODIFY COLUMN ...")


def cmd_dump(args):
    if _storage is None:
        _err("No database open")
        return
    if not args:
        _err("Usage: DUMP PAGE <id>")
        return
    try:
        pid = int(args[-1])
        data = _storage.read_page(pid)
        h = read_page_header(data)
        print(f"\n  Page {pid}:")
        for k, v in h.items():
            print(f"    {k}: {v}")
        print(f"    free_space: {free_space(data)} bytes")
        print(f"    slots:")
        for slot_idx, rec in iter_slots(data):
            print(f"      [{slot_idx}] {rec.hex()} ({len(rec)} bytes)")
    except Exception as exc:
        _err(str(exc))


def cmd_count(args):
    if _executor is None:
        _err("No database open")
        return
    import re
    raw = ' '.join(args)
    m = re.match(r'FROM\s+(\w+)(?:\s+WHERE\s+(.+))?$', raw, re.IGNORECASE)
    if not m:
        _err("Usage: COUNT FROM table [WHERE cond]")
        return
    name  = m.group(1)
    where = m.group(2)
    sql = f"SELECT COUNT(*) FROM {name}"
    if where:
        sql += f" WHERE {where}"
    _run_sql(sql)


def cmd_help(args):
    print("""
  Database Commands:
    OPEN <file>                         open or create a .vyndb file
    CLOSE                               close the current database

  DDL:
    CREATE TABLE name (col type, ...)   create a table
    DROP TABLE name                     drop a table
    CREATE INDEX name ON table (col)    create a B-tree index
    DESCRIBE table                      show table schema and info

  DML:
    INSERT INTO table VALUES (v, ...)   insert a row
    SELECT cols FROM table              query rows
      [WHERE col op val]
      [ORDER BY col [DESC]]
      [LIMIT n] [OFFSET n]
    UPDATE table SET col=val            update rows
      [WHERE cond]
    DELETE FROM table                   delete rows
      [WHERE cond]
    COUNT FROM table [WHERE cond]       count rows

  Inspection:
    TABLES                              list all tables
    PAGES                               show all pages in the file
    DUMP PAGE <id>                      dump raw page contents

  Shell:
    HELP                                show this message
    HISTORY                             show command history
    CLEAR                               clear the screen
    EXIT / QUIT                         exit the shell

  Supported types: INT  FLOAT  BOOL  TEXT  VARCHAR
  Supported WHERE ops: =  !=  >  <  >=  <=
""")


def cmd_history(args):
    if not _history:
        _info("No history")
        return
    for i, h in enumerate(_history):
        print(f"  {i+1:3}  {h}")


def cmd_clear(args):
    os.system('cls' if os.name == 'nt' else 'clear')
    _print_banner()


COMMANDS = {
    'OPEN':   cmd_open,
    'CLOSE':  cmd_close,
    'CREATE': None,
    'DROP':   cmd_drop_database,
    'INSERT': cmd_insert,
    'SELECT': cmd_select,
    'UPDATE': cmd_update,
    'DELETE': cmd_delete,
    'COUNT':  cmd_count,
    'DESCRIBE': cmd_describe,
    'TABLES': cmd_tables,
    'PAGES':  cmd_pages,
    'DUMP':   cmd_dump,
    'HELP':   cmd_help,
    'HISTORY':cmd_history,
    'CLEAR':  cmd_clear,
}


SQL_STARTERS = {
    'SELECT', 'INSERT', 'UPDATE', 'DELETE',
    'CREATE', 'DROP', 'ALTER', 'TRUNCATE',
    'BEGIN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT',
    'EXPLAIN',
}

def _dispatch(line):
    stripped = line.strip()
    if not stripped:
        return

    tokens = stripped.split()
    cmd = tokens[0].upper()
    rest = tokens[1:]

    # Shell-only commands — never go through query engine
    if cmd == 'OPEN':
        cmd_open(rest)
        return
    if cmd == 'CLOSE':
        cmd_close(rest)
        return
    if cmd == 'TABLES':
        cmd_tables(rest)
        return
    if cmd == 'PAGES':
        cmd_pages(rest)
        return
    if cmd == 'DUMP':
        cmd_dump(rest)
        return
    if cmd == 'DESCRIBE':
        cmd_describe(rest)
        return
    if cmd == 'COUNT':
        cmd_count(rest)
        return
    if cmd == 'HELP':
        cmd_help(rest)
        return
    if cmd == 'HISTORY':
        cmd_history(rest)
        return
    if cmd == 'CLEAR':
        cmd_clear(rest)
        return

    # DROP with no subcommand = drop database
    if cmd == 'DROP' and (not rest or rest[0].upper() not in ('TABLE', 'INDEX')):
        cmd_drop_database(rest)
        return

    # Everything else goes through the query engine
    if cmd in SQL_STARTERS:
        _run_sql(stripped)
        return

    _err(f"Unknown command '{cmd}'. Type HELP for commands.")


def _read_multiline():
    lines = []
    while True:
        try:
            if not lines:
                line = input(PROMPT)
            else:
                line = input(CONTINUATION)
        except EOFError:
            break
        if not line.strip():
            if lines:
                continue
            return ''
        lines.append(line)
        joined = ' '.join(lines)
        if not joined.strip().endswith('\\'):
            return joined
        lines[-1] = line.rstrip('\\')


def main():
    _print_banner()
    if len(sys.argv) > 1:
        cmd_open([sys.argv[1]])

    while True:
        try:
            line = _read_multiline()
        except KeyboardInterrupt:
            print()
            continue

        if not line:
            continue

        stripped = line.strip()
        if stripped.upper() in ('EXIT', 'QUIT'):
            if _storage:
                cmd_close([])
            print("  Bye.")
            break

        _history.append(stripped)
        try:
            _dispatch(stripped)
        except Exception as exc:
            _err(f"Error: {exc}")
            if os.environ.get('VYNDB_DEBUG'):
                import traceback
                traceback.print_exc()


if __name__ == '__main__':
    main()