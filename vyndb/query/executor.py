import struct
import fnmatch
from query.parser import (
    Column, Star, Literal, BinaryOp, UnaryOp, FunctionCall,
    CaseNode, InNode, BetweenNode, IsNullNode, LikeNode,
    SubqueryNode, OrderByItem, SelectNode
)
from query.planner import (
    SeqScan, IndexScan, ProjectNode, FilterNode, SortNode,
    LimitNode, AggregateNode, NestedLoopJoin,
    InsertPlan, UpdatePlan, DeletePlan,
    CreateTablePlan, DropTablePlan, CreateIndexPlan, DropIndexPlan,
    AlterTablePlan, TruncatePlan, TxPlan, ExplainPlan, Planner
)
from catalog.schema import ColumnDef, IndexDef, TableDef
from engine.page import (
    PAGE_TYPE_DATA, PAGE_HEADER_SIZE, PAGE_SIZE,
    read_page_header, write_page_header,
    insert_slot, read_slot, delete_slot, iter_slots,
    free_space, make_page, set_checksum
)
from engine.btree import BTree, RID


class ExecutionError(Exception):
    pass


class Executor:
    def __init__(self, catalog, pool, storage):
        self._catalog = catalog
        self._pool    = pool
        self._storage = storage
        self._tx_active    = False
        self._savepoints   = {}
        self._planner      = Planner(catalog)

    def execute(self, plan):
        if isinstance(plan, ExplainPlan):
            return [{'plan': self._planner.describe(plan.inner)}]
        if isinstance(plan, TxPlan):
            return self._exec_tx(plan)
        if isinstance(plan, CreateTablePlan):
            return self._exec_create_table(plan)
        if isinstance(plan, DropTablePlan):
            return self._exec_drop_table(plan)
        if isinstance(plan, CreateIndexPlan):
            return self._exec_create_index(plan)
        if isinstance(plan, DropIndexPlan):
            return self._exec_drop_index(plan)
        if isinstance(plan, AlterTablePlan):
            return self._exec_alter_table(plan)
        if isinstance(plan, TruncatePlan):
            return self._exec_truncate(plan)
        if isinstance(plan, InsertPlan):
            return self._exec_insert(plan)
        if isinstance(plan, UpdatePlan):
            return self._exec_update(plan)
        if isinstance(plan, DeletePlan):
            return self._exec_delete(plan)
        if isinstance(plan, (ProjectNode, SeqScan, IndexScan,
                             FilterNode, SortNode, LimitNode,
                             AggregateNode, NestedLoopJoin)):
            return list(self._eval_plan(plan, {}))
        raise ExecutionError(f"Unknown plan type {type(plan).__name__}")

    def _exec_tx(self, plan):
        op = plan.operation
        if op == 'BEGIN':
            self._tx_active = True
            self._savepoints = {}
        elif op == 'COMMIT':
            self._pool.flush_all()
            self._tx_active = False
        elif op == 'ROLLBACK':
            self._tx_active = False
        elif op == 'SAVEPOINT':
            self._savepoints[plan.savepoint] = True
        return [{'status': op}]

    def _exec_create_table(self, plan):
        node = plan.node
        page_id, frame = self._pool.new_page(PAGE_TYPE_DATA)
        self._pool.unpin(page_id, dirty=True)
        self._pool.flush(page_id)
        columns = []
        for c in node.columns:
            col = ColumnDef(
                name        = c['name'],
                col_type    = c['type'],
                primary_key = c.get('primary_key', False),
                nullable    = c.get('nullable', True),
                unique      = c.get('unique', False),
                default     = c.get('default'),
            )
            columns.append(col)
        table_def = TableDef(node.table, columns, page_id)
        self._catalog.create_table(table_def)
        return [{'status': f"Table '{node.table}' created"}]

    def _exec_drop_table(self, plan):
        self._catalog.drop_table(plan.table)
        return [{'status': f"Table '{plan.table}' dropped"}]

    def _exec_create_index(self, plan):
        node = plan.node
        table_def = self._catalog.get_table(node.table)
        if table_def is None:
            raise ExecutionError(f"Table '{node.table}' does not exist")
        col = table_def.get_column(node.column)
        if col is None:
            raise ExecutionError(f"Column '{node.column}' does not exist")
        tree = BTree(self._pool)
        root = tree.init()
        for row in self._full_scan(table_def):
            val = row.get(node.column)
            if val is not None:
                try:
                    key = int(float(str(val)))
                    tree.insert(key, RID(table_def.root_page, 0))
                except (ValueError, TypeError):
                    pass
        idx = IndexDef(node.name, node.table, node.column, root, node.unique)
        self._catalog.add_index(node.table, idx)
        return [{'status': f"Index '{node.name}' created on '{node.table}.{node.column}'"}]

    def _exec_drop_index(self, plan):
        self._catalog.drop_index(plan.table, plan.name)
        return [{'status': f"Index '{plan.name}' dropped"}]

    def _exec_alter_table(self, plan):
        node = plan.node
        op   = node.operation
        payload = node.payload
        if op == 'ADD COLUMN':
            col = ColumnDef(
                name        = payload['name'],
                col_type    = payload['type'],
                primary_key = payload.get('primary_key', False),
                nullable    = payload.get('nullable', True),
                unique      = payload.get('unique', False),
                default     = payload.get('default'),
            )
            self._catalog.add_column(node.table, col)
        elif op == 'DROP COLUMN':
            self._catalog.drop_column(node.table, payload['col_name'])
        elif op == 'RENAME COLUMN':
            self._catalog.rename_column(node.table, payload['old_name'], payload['new_name'])
        elif op == 'RENAME TO':
            self._catalog.rename_table(node.table, payload['new_name'])
        elif op == 'MODIFY COLUMN':
            self._catalog.modify_column(node.table, payload['name'],
                                        new_type=payload.get('type'))
        return [{'status': f"ALTER TABLE {node.table} {op} OK"}]

    def _exec_truncate(self, plan):
        table_def = self._catalog.get_table(plan.table)
        if table_def is None:
            raise ExecutionError(f"Table '{plan.table}' does not exist")
        page_id = table_def.root_page
        while page_id != 0xFFFFFFFF:
            frame = self._pool.fetch(page_id)
            h = read_page_header(frame.data)
            next_pid = h['next_page_id']
            self._pool.unpin(page_id)
            if page_id != table_def.root_page:
                self._storage.free_page(page_id)
            page_id = next_pid
        new_page = make_page(table_def.root_page, PAGE_TYPE_DATA)
        set_checksum(new_page)
        self._storage.write_page(table_def.root_page, new_page)
        self._pool.invalidate(table_def.root_page)
        self._catalog.set_row_count(plan.table, 0)
        return [{'status': f"Table '{plan.table}' truncated"}]

    def _exec_insert(self, plan):
        table_def = self._catalog.get_table(plan.table)
        if table_def is None:
            raise ExecutionError(f"Table '{plan.table}' does not exist")
        inserted = 0
        for value_row in plan.values:
            row = {}
            if plan.columns:
                if len(plan.columns) != len(value_row):
                    raise ExecutionError("Column count does not match value count")
                for col_name, expr in zip(plan.columns, value_row):
                    row[col_name] = self._eval_expr(expr, {})
            else:
                if len(value_row) != len(table_def.columns):
                    raise ExecutionError("Value count does not match column count")
                for col, expr in zip(table_def.columns, value_row):
                    row[col.name] = self._eval_expr(expr, {})
            for col in table_def.columns:
                if col.name not in row:
                    if col.default is not None:
                        row[col.name] = col.default
                    elif not col.nullable:
                        raise ExecutionError(f"Column '{col.name}' cannot be NULL")
                    else:
                        row[col.name] = None
            packed = self._pack_row(row, table_def)
            self._write_row(packed, table_def)
            inserted += 1
        self._catalog.update_row_count(plan.table, inserted)
        return [{'inserted': inserted}]

    def _exec_update(self, plan):
        table_def = self._catalog.get_table(plan.table)
        if table_def is None:
            raise ExecutionError(f"Table '{plan.table}' does not exist")
        updated = 0
        page_id = table_def.root_page
        while page_id != 0xFFFFFFFF:
            frame = self._pool.fetch(page_id)
            h = read_page_header(frame.data)
            dirty = False
            for slot_idx, rec in list(iter_slots(frame.data)):
                row = self._unpack_row(rec, table_def)
                if plan.predicate is None or self._eval_expr(plan.predicate, row):
                    for col_name, expr in plan.assignments:
                        row[col_name] = self._eval_expr(expr, row)
                    packed = self._pack_row(row, table_def)
                    delete_slot(frame.data, slot_idx)
                    insert_slot(frame.data, packed)
                    updated += 1
                    dirty = True
            next_pid = h['next_page_id']
            self._pool.unpin(page_id, dirty=dirty)
            if dirty:
                self._pool.flush(page_id)
            page_id = next_pid
        return [{'updated': updated}]

    def _exec_delete(self, plan):
        table_def = self._catalog.get_table(plan.table)
        if table_def is None:
            raise ExecutionError(f"Table '{plan.table}' does not exist")
        deleted = 0
        page_id = table_def.root_page
        while page_id != 0xFFFFFFFF:
            frame = self._pool.fetch(page_id)
            h = read_page_header(frame.data)
            dirty = False
            for slot_idx, rec in list(iter_slots(frame.data)):
                row = self._unpack_row(rec, table_def)
                if plan.predicate is None or self._eval_expr(plan.predicate, row):
                    delete_slot(frame.data, slot_idx)
                    deleted += 1
                    dirty = True
            next_pid = h['next_page_id']
            self._pool.unpin(page_id, dirty=dirty)
            if dirty:
                self._pool.flush(page_id)
            page_id = next_pid
        self._catalog.update_row_count(plan.table, -deleted)
        return [{'deleted': deleted}]

    def _eval_plan(self, plan, ctx):
        if isinstance(plan, SeqScan):
            yield from self._eval_seqscan(plan, ctx)
        elif isinstance(plan, IndexScan):
            yield from self._eval_indexscan(plan, ctx)
        elif isinstance(plan, ProjectNode):
            yield from self._eval_project(plan, ctx)
        elif isinstance(plan, FilterNode):
            for row in self._eval_plan(plan.child, ctx):
                if self._eval_expr(plan.predicate, row):
                    yield row
        elif isinstance(plan, SortNode):
            rows = list(self._eval_plan(plan.child, ctx))
            for item in reversed(plan.order_by):
                rows.sort(
                    key=lambda r: (self._eval_expr(item.expr, r) is None,
                                   self._eval_expr(item.expr, r) or ''),
                    reverse=item.descending
                )
            yield from rows
        elif isinstance(plan, LimitNode):
            offset = int(self._eval_expr(plan.offset, {}) or 0) if plan.offset else 0
            limit  = int(self._eval_expr(plan.limit, {}) or 0) if plan.limit else None
            rows = self._eval_plan(plan.child, ctx)
            count = 0
            skipped = 0
            for row in rows:
                if skipped < offset:
                    skipped += 1
                    continue
                yield row
                count += 1
                if limit is not None and count >= limit:
                    break
        elif isinstance(plan, AggregateNode):
            yield from self._eval_aggregate(plan, ctx)
        elif isinstance(plan, NestedLoopJoin):
            yield from self._eval_join(plan, ctx)

    def _eval_seqscan(self, plan, ctx):
        if plan.table is None:
            yield {}
            return
        if isinstance(plan.table, SubqueryNode):
            sub_plan = self._planner.plan(plan.table.select_node)
            for row in self._eval_plan(sub_plan, ctx):
                if plan.alias:
                    yield {f"{plan.alias}.{k}": v for k, v in row.items()}
                else:
                    yield row
            return
        table_def = self._catalog.get_table(plan.table)
        if table_def is None:
            raise ExecutionError(f"Table '{plan.table}' does not exist")
        prefix = f"{plan.alias}." if plan.alias else ''
        for row in self._full_scan(table_def):
            prefixed = {f"{prefix}{k}": v for k, v in row.items()} if prefix else row
            if plan.predicate is None or self._eval_expr(plan.predicate, prefixed):
                yield prefixed

    def _eval_indexscan(self, plan, ctx):
        table_def = self._catalog.get_table(plan.table)
        if table_def is None:
            raise ExecutionError(f"Table '{plan.table}' does not exist")
        idx_def = table_def.indexes.get(plan.index_name)
        if idx_def is None:
            yield from self._eval_seqscan(
                SeqScan(plan.table, plan.alias, None), ctx)
            return
        prefix = f"{plan.alias}." if plan.alias else ''
        for row in self._full_scan(table_def):
            val = row.get(plan.col)
            try:
                row_val = float(str(val)) if val is not None else None
                cmp_val = float(str(plan.value))
            except (ValueError, TypeError):
                row_val = str(val) if val is not None else None
                cmp_val = str(plan.value)
            match = False
            if row_val is None:
                pass
            elif plan.op == '=':  match = row_val == cmp_val
            elif plan.op == '<':  match = row_val <  cmp_val
            elif plan.op == '>':  match = row_val >  cmp_val
            elif plan.op == '<=': match = row_val <= cmp_val
            elif plan.op == '>=': match = row_val >= cmp_val
            if match:
                yield {f"{prefix}{k}": v for k, v in row.items()} if prefix else row

    def _eval_project(self, plan, ctx):
        for row in self._eval_plan(plan.child, ctx):
            out = {}
            for col_expr in plan.columns:
                if isinstance(col_expr, Star):
                    if col_expr.table:
                        for k, v in row.items():
                            if k.startswith(col_expr.table + '.'):
                                out[k.split('.', 1)[1]] = v
                    else:
                        out.update(row)
                elif isinstance(col_expr, Column):
                    key = f"{col_expr.table}.{col_expr.name}" if col_expr.table else col_expr.name
                    val = row.get(key, row.get(col_expr.name))
                    label = col_expr.alias or col_expr.name
                    out[label] = val
                else:
                    val = self._eval_expr(col_expr, row)
                    if isinstance(col_expr, FunctionCall):
                        label = col_expr.name
                    else:
                        label = str(col_expr)
                    out[label] = val
            yield out

    def _eval_aggregate(self, plan, ctx):
        rows = list(self._eval_plan(plan.child, ctx))
        AGG_FUNCS = {'COUNT', 'SUM', 'AVG', 'MIN', 'MAX'}

        def _group_key(row):
            if not plan.group_by:
                return ()
            return tuple(self._eval_expr(e, row) for e in plan.group_by)

        groups = {}
        for row in rows:
            k = _group_key(row)
            groups.setdefault(k, []).append(row)

        if not groups:
            groups[()] = []

        for key, group_rows in groups.items():
            out = {}
            if plan.group_by:
                for expr, val in zip(plan.group_by, key):
                    if isinstance(expr, Column):
                        out[expr.alias or expr.name] = val

            for col_expr in plan.columns:
                if isinstance(col_expr, FunctionCall) and col_expr.name in AGG_FUNCS:
                    fname = col_expr.name
                    arg   = col_expr.args[0] if col_expr.args else None
                    vals  = []
                    for r in group_rows:
                        if arg is None or isinstance(arg, Star):
                            vals.append(1)
                        else:
                            v = self._eval_expr(arg, r)
                            if v is not None:
                                vals.append(v)
                    if fname == 'COUNT':
                        result = len(group_rows) if (arg is None or isinstance(arg, Star)) else len(vals)
                    elif fname == 'SUM':
                        result = sum(vals) if vals else None
                    elif fname == 'AVG':
                        result = sum(vals) / len(vals) if vals else None
                    elif fname == 'MIN':
                        result = min(vals) if vals else None
                    elif fname == 'MAX':
                        result = max(vals) if vals else None
                    label = col_expr.name
                    out[label] = result
                elif isinstance(col_expr, Column):
                    if col_expr.name not in out:
                        val = self._eval_expr(col_expr, group_rows[0]) if group_rows else None
                        out[col_expr.alias or col_expr.name] = val
                elif isinstance(col_expr, Star):
                    if group_rows:
                        out.update(group_rows[0])

            if plan.having is None or self._eval_expr(plan.having, out):
                yield out

    def _eval_join(self, plan, ctx):
        left_rows  = list(self._eval_plan(plan.left, ctx))
        right_rows = list(self._eval_plan(plan.right, ctx))
        jtype = plan.join_type.upper()

        for lr in left_rows:
            matched = False
            for rr in right_rows:
                combined = {**lr, **rr}
                if plan.condition is None or self._eval_expr(plan.condition, combined):
                    matched = True
                    yield combined
            if not matched and jtype in ('LEFT', 'FULL'):
                nulled = {k: None for k in (right_rows[0] if right_rows else {})}
                yield {**lr, **nulled}

        if jtype in ('RIGHT', 'FULL'):
            for rr in right_rows:
                matched = any(
                    self._eval_expr(plan.condition, {**lr, **rr}) if plan.condition else True
                    for lr in left_rows
                )
                if not matched:
                    nulled = {k: None for k in (left_rows[0] if left_rows else {})}
                    yield {**nulled, **rr}

    def _full_scan(self, table_def):
        page_id = table_def.root_page
        while page_id != 0xFFFFFFFF:
            frame = self._pool.fetch(page_id)
            h = read_page_header(frame.data)
            for _, rec in iter_slots(frame.data):
                yield self._unpack_row(rec, table_def)
            next_pid = h['next_page_id']
            self._pool.unpin(page_id)
            page_id = next_pid

    def _write_row(self, packed, table_def):
        page_id = table_def.root_page
        while True:
            frame = self._pool.fetch(page_id)
            h = read_page_header(frame.data)
            if free_space(frame.data) >= len(packed) + 4:
                insert_slot(frame.data, packed)
                self._pool.unpin(page_id, dirty=True)
                self._pool.flush(page_id)
                return
            next_pid = h['next_page_id']
            self._pool.unpin(page_id)
            if next_pid == 0xFFFFFFFF:
                new_pid, new_frame = self._pool.new_page(PAGE_TYPE_DATA)
                frame2 = self._pool.fetch(page_id)
                h2 = read_page_header(frame2.data)
                h2['next_page_id'] = new_pid
                write_page_header(frame2.data, h2)
                set_checksum(frame2.data)
                self._pool.unpin(page_id, dirty=True)
                self._pool.flush(page_id)
                insert_slot(new_frame.data, packed)
                self._pool.unpin(new_pid, dirty=True)
                self._pool.flush(new_pid)
                return
            page_id = next_pid

    def _pack_row(self, row, table_def):
        parts = []
        for col in table_def.columns:
            val = row.get(col.name)
            ct  = col.col_type
            if ct == 'INT':
                parts.append(struct.pack('<q', int(val) if val is not None else 0))
            elif ct == 'FLOAT':
                parts.append(struct.pack('<d', float(val) if val is not None else 0.0))
            elif ct == 'BOOL':
                parts.append(struct.pack('<B', 1 if val else 0))
            else:
                s = str(val) if val is not None else ''
                enc = s.encode('utf-8')[:65535]
                parts.append(struct.pack('<H', len(enc)) + enc)
        return b''.join(parts)

    def _unpack_row(self, data, table_def):
        row    = {}
        offset = 0
        for col in table_def.columns:
            ct = col.col_type
            if ct == 'INT':
                val, = struct.unpack_from('<q', data, offset)
                offset += 8
                row[col.name] = val
            elif ct == 'FLOAT':
                val, = struct.unpack_from('<d', data, offset)
                offset += 8
                row[col.name] = val
            elif ct == 'BOOL':
                val, = struct.unpack_from('<B', data, offset)
                offset += 1
                row[col.name] = bool(val)
            else:
                length, = struct.unpack_from('<H', data, offset)
                offset += 2
                row[col.name] = data[offset:offset + length].decode('utf-8')
                offset += length
        return row

    def _eval_expr(self, expr, row):
        if expr is None:
            return None
        if isinstance(expr, Literal):
            return expr.value
        if isinstance(expr, Column):
            key = f"{expr.table}.{expr.name}" if expr.table else expr.name
            return row.get(key, row.get(expr.name))
        if isinstance(expr, Star):
            return row
        if isinstance(expr, BinaryOp):
            return self._eval_binary(expr, row)
        if isinstance(expr, UnaryOp):
            val = self._eval_expr(expr.operand, row)
            if expr.op == '-':
                return -val if val is not None else None
            if expr.op == 'NOT':
                return not val
        if isinstance(expr, FunctionCall):
            return self._eval_function(expr, row)
        if isinstance(expr, CaseNode):
            for cond, result in expr.whens:
                if self._eval_expr(cond, row):
                    return self._eval_expr(result, row)
            return self._eval_expr(expr.else_expr, row)
        if isinstance(expr, IsNullNode):
            val = self._eval_expr(expr.expr, row)
            result = val is None
            return not result if expr.negated else result
        if isinstance(expr, LikeNode):
            val     = self._eval_expr(expr.expr, row)
            pattern = self._eval_expr(expr.pattern, row)
            if val is None or pattern is None:
                return False
            py_pat = pattern.replace('%', '*').replace('_', '?')
            result  = fnmatch.fnmatch(str(val), py_pat)
            return not result if expr.negated else result
        if isinstance(expr, InNode):
            val = self._eval_expr(expr.expr, row)
            values = [self._eval_expr(v, row) for v in expr.values]
            result = val in values
            return not result if expr.negated else result
        if isinstance(expr, BetweenNode):
            val  = self._eval_expr(expr.expr, row)
            low  = self._eval_expr(expr.low, row)
            high = self._eval_expr(expr.high, row)
            if val is None:
                return False
            result = low <= val <= high
            return not result if expr.negated else result
        if isinstance(expr, SubqueryNode):
            sub_plan = self._planner.plan(expr.select_node)
            rows = list(self._eval_plan(sub_plan, row))
            if rows:
                return list(rows[0].values())[0]
            return None
        return expr

    def _eval_binary(self, expr, row):
        op = expr.op
        if op == 'AND':
            return bool(self._eval_expr(expr.left, row)) and bool(self._eval_expr(expr.right, row))
        if op == 'OR':
            return bool(self._eval_expr(expr.left, row)) or bool(self._eval_expr(expr.right, row))
        left  = self._eval_expr(expr.left, row)
        right = self._eval_expr(expr.right, row)
        if op == '=':  return left == right
        if op == '!=': return left != right
        if op == '<':  return left is not None and right is not None and left < right
        if op == '>':  return left is not None and right is not None and left > right
        if op == '<=': return left is not None and right is not None and left <= right
        if op == '>=': return left is not None and right is not None and left >= right
        if op == '+':
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return (left or 0) + (right or 0)
        if op == '-':  return (left or 0) - (right or 0)
        if op == '*':  return (left or 0) * (right or 0)
        if op == '/':
            if right == 0:
                raise ExecutionError("Division by zero")
            return (left or 0) / right
        if op == '%':  return (left or 0) % (right or 0)
        if op == '||': return str(left or '') + str(right or '')
        raise ExecutionError(f"Unknown operator '{op}'")

    def _eval_function(self, expr, row):
        name = expr.name.upper()
        if name == 'COALESCE':
            for arg in expr.args:
                v = self._eval_expr(arg, row)
                if v is not None:
                    return v
            return None
        if name == 'NULLIF':
            a = self._eval_expr(expr.args[0], row)
            b = self._eval_expr(expr.args[1], row)
            return None if a == b else a
        if name == 'CAST':
            val  = self._eval_expr(expr.args[0], row)
            typ  = self._eval_expr(expr.args[1], row) if len(expr.args) > 1 else None
            if typ is None:
                return val
            t = str(typ).upper()
            if t == 'INT':    return int(val) if val is not None else None
            if t == 'FLOAT':  return float(val) if val is not None else None
            if t == 'TEXT':   return str(val) if val is not None else None
            if t == 'BOOL':   return bool(val)
            return val
        if name in ('COUNT', 'SUM', 'AVG', 'MIN', 'MAX'):
            return None
        raise ExecutionError(f"Unknown function '{name}'")