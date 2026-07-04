import struct

SUPPORTED_TYPES = ('INT', 'FLOAT', 'BOOL', 'TEXT', 'VARCHAR', 'BLOB')

COL_FLAG_PRIMARY  = 0x01
COL_FLAG_NULLABLE = 0x02
COL_FLAG_UNIQUE   = 0x04
COL_FLAG_INDEXED  = 0x08


class ColumnDef:
    def __init__(self, name, col_type, primary_key=False,
                 nullable=True, unique=False, default=None):
        self.name        = name
        self.col_type    = col_type.upper()
        self.primary_key = primary_key
        self.nullable    = nullable
        self.unique      = unique
        self.default     = default

        if self.col_type not in SUPPORTED_TYPES:
            raise ValueError(f"Unsupported column type '{col_type}'")

    def flags(self):
        f = 0
        if self.primary_key: f |= COL_FLAG_PRIMARY
        if self.nullable:    f |= COL_FLAG_NULLABLE
        if self.unique:      f |= COL_FLAG_UNIQUE
        return f

    def pack(self):
        name_enc    = self.name.encode('utf-8')
        type_enc    = self.col_type.encode('utf-8')
        default_enc = (str(self.default) if self.default is not None else '').encode('utf-8')
        return (
            struct.pack('<HH', len(name_enc), len(type_enc)) +
            name_enc +
            type_enc +
            struct.pack('<BH', self.flags(), len(default_enc)) +
            default_enc
        )

    @classmethod
    def unpack(cls, data, offset):
        name_len, type_len = struct.unpack_from('<HH', data, offset)
        offset += 4
        name     = data[offset:offset + name_len].decode('utf-8')
        offset  += name_len
        col_type = data[offset:offset + type_len].decode('utf-8')
        offset  += type_len
        flags, default_len = struct.unpack_from('<BH', data, offset)
        offset  += 3
        default_raw = data[offset:offset + default_len].decode('utf-8')
        offset  += default_len
        default = default_raw if default_raw else None
        return cls(
            name        = name,
            col_type    = col_type,
            primary_key = bool(flags & COL_FLAG_PRIMARY),
            nullable    = bool(flags & COL_FLAG_NULLABLE),
            unique      = bool(flags & COL_FLAG_UNIQUE),
            default     = default,
        ), offset

    def to_dict(self):
        return {
            'name':        self.name,
            'type':        self.col_type,
            'primary_key': self.primary_key,
            'nullable':    self.nullable,
            'unique':      self.unique,
            'default':     self.default,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            name        = d['name'],
            col_type    = d['type'],
            primary_key = d.get('primary_key', False),
            nullable    = d.get('nullable', True),
            unique      = d.get('unique', False),
            default     = d.get('default'),
        )

    def __repr__(self):
        flags = []
        if self.primary_key: flags.append('PK')
        if self.unique:      flags.append('UNIQUE')
        if not self.nullable: flags.append('NOT NULL')
        if self.default is not None: flags.append(f'DEFAULT={self.default}')
        suffix = ' ' + ' '.join(flags) if flags else ''
        return f"<Column {self.name} {self.col_type}{suffix}>"


class IndexDef:
    def __init__(self, name, table_name, column_name,
                 root_page, unique=False):
        self.name        = name
        self.table_name  = table_name
        self.column_name = column_name
        self.root_page   = root_page
        self.unique      = unique

    def pack(self):
        n  = self.name.encode('utf-8')
        t  = self.table_name.encode('utf-8')
        c  = self.column_name.encode('utf-8')
        return (
            struct.pack('<HHHIB',
                len(n), len(t), len(c),
                self.root_page,
                1 if self.unique else 0) +
            n + t + c
        )

    @classmethod
    def unpack(cls, data, offset):
        nl, tl, cl, root_page, unique = struct.unpack_from('<HHHIB', data, offset)
        offset += 11
        name       = data[offset:offset + nl].decode('utf-8'); offset += nl
        table_name = data[offset:offset + tl].decode('utf-8'); offset += tl
        col_name   = data[offset:offset + cl].decode('utf-8'); offset += cl
        return cls(name, table_name, col_name, root_page, bool(unique)), offset

    def to_dict(self):
        return {
            'name':        self.name,
            'table_name':  self.table_name,
            'column_name': self.column_name,
            'root_page':   self.root_page,
            'unique':      self.unique,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            d['name'], d['table_name'], d['column_name'],
            d['root_page'], d.get('unique', False)
        )

    def __repr__(self):
        u = ' UNIQUE' if self.unique else ''
        return f"<Index {self.name}{u} on {self.table_name}.{self.column_name} root={self.root_page}>"


class TableDef:
    def __init__(self, name, columns, root_page,
                 row_count=0, indexes=None):
        self.name       = name
        self.columns    = columns
        self.root_page  = root_page
        self.row_count  = row_count
        self.indexes    = indexes or {}

    def get_column(self, name):
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def column_names(self):
        return [c.name for c in self.columns]

    def primary_key_col(self):
        for c in self.columns:
            if c.primary_key:
                return c
        return None

    def add_column(self, col_def, position=None):
        if self.get_column(col_def.name):
            raise ValueError(f"Column '{col_def.name}' already exists")
        if position is None:
            self.columns.append(col_def)
        else:
            self.columns.insert(position, col_def)

    def drop_column(self, name):
        col = self.get_column(name)
        if col is None:
            raise ValueError(f"Column '{name}' does not exist")
        if col.primary_key:
            raise ValueError(f"Cannot drop primary key column '{name}'")
        self.columns = [c for c in self.columns if c.name != name]

    def rename_column(self, old_name, new_name):
        col = self.get_column(old_name)
        if col is None:
            raise ValueError(f"Column '{old_name}' does not exist")
        if self.get_column(new_name):
            raise ValueError(f"Column '{new_name}' already exists")
        col.name = new_name
        for idx in self.indexes.values():
            if idx.column_name == old_name:
                idx.column_name = new_name

    def modify_column(self, name, new_type=None, nullable=None,
                      unique=None, default=None):
        col = self.get_column(name)
        if col is None:
            raise ValueError(f"Column '{name}' does not exist")
        if new_type is not None:
            if new_type.upper() not in SUPPORTED_TYPES:
                raise ValueError(f"Unsupported type '{new_type}'")
            col.col_type = new_type.upper()
        if nullable is not None:
            col.nullable = nullable
        if unique is not None:
            col.unique = unique
        if default is not None:
            col.default = default

    def pack(self):
        name_enc = self.name.encode('utf-8')
        col_data = b''.join(c.pack() for c in self.columns)
        idx_data = b''.join(i.pack() for i in self.indexes.values())
        return (
            struct.pack('<H',  len(name_enc)) + name_enc +
            struct.pack('<III', self.root_page, self.row_count, len(self.columns)) +
            col_data +
            struct.pack('<I', len(self.indexes)) +
            idx_data
        )

    @classmethod
    def unpack(cls, data, offset):
        name_len, = struct.unpack_from('<H', data, offset); offset += 2
        name = data[offset:offset + name_len].decode('utf-8'); offset += name_len
        root_page, row_count, col_count = struct.unpack_from('<III', data, offset)
        offset += 12
        columns = []
        for _ in range(col_count):
            col, offset = ColumnDef.unpack(data, offset)
            columns.append(col)
        idx_count, = struct.unpack_from('<I', data, offset); offset += 4
        indexes = {}
        for _ in range(idx_count):
            idx, offset = IndexDef.unpack(data, offset)
            indexes[idx.name] = idx
        return cls(name, columns, root_page, row_count, indexes), offset

    def to_dict(self):
        return {
            'name':       self.name,
            'columns':    [c.to_dict() for c in self.columns],
            'root_page':  self.root_page,
            'row_count':  self.row_count,
            'indexes':    {k: v.to_dict() for k, v in self.indexes.items()},
        }

    @classmethod
    def from_dict(cls, d):
        columns = [ColumnDef.from_dict(c) for c in d['columns']]
        indexes = {k: IndexDef.from_dict(v) for k, v in d.get('indexes', {}).items()}
        return cls(d['name'], columns, d['root_page'], d.get('row_count', 0), indexes)

    def __repr__(self):
        return f"<Table {self.name} cols={self.column_names()} rows={self.row_count}>"