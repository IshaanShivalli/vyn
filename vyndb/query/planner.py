from query.parser import (
    SelectNode, InsertNode, UpdateNode, DeleteNode,
    CreateTableNode, DropTableNode, CreateIndexNode, DropIndexNode,
    AlterTableNode, BeginNode, CommitNode, RollbackNode, SavepointNode,
    ExplainNode, TruncateNode, Column, Star, FunctionCall, BinaryOp,
    Literal, SubqueryNode
)


class PlanNode:
    pass


class SeqScan(PlanNode):
    def __init__(self, table, alias, predicate):
        self.table     = table
        self.alias     = alias
        self.predicate = predicate


class IndexScan(PlanNode):
    def __init__(self, table, alias, index_name, col, op, value):
        self.table      = table
        self.alias      = alias
        self.index_name = index_name
        self.col        = col
        self.op         = op
        self.value      = value


class NestedLoopJoin(PlanNode):
    def __init__(self, left, right, condition, join_type):
        self.left      = left
        self.right     = right
        self.condition = condition
        self.join_type = join_type


class ProjectNode(PlanNode):
    def __init__(self, child, columns):
        self.child   = child
        self.columns = columns


class FilterNode(PlanNode):
    def __init__(self, child, predicate):
        self.child     = child
        self.predicate = predicate


class SortNode(PlanNode):
    def __init__(self, child, order_by):
        self.child    = child
        self.order_by = order_by


class LimitNode(PlanNode):
    def __init__(self, child, limit, offset):
        self.child  = child
        self.limit  = limit
        self.offset = offset


class AggregateNode(PlanNode):
    def __init__(self, child, group_by, aggregates, having):
        self.child      = child
        self.group_by   = group_by
        self.aggregates = aggregates
        self.having     = having


class InsertPlan(PlanNode):
    def __init__(self, table, columns, values):
        self.table   = table
        self.columns = columns
        self.values  = values


class UpdatePlan(PlanNode):
    def __init__(self, scan, table, assignments, predicate):
        self.scan        = scan
        self.table       = table
        self.assignments = assignments
        self.predicate   = predicate


class DeletePlan(PlanNode):
    def __init__(self, scan, table, predicate):
        self.scan      = scan
        self.table     = table
        self.predicate = predicate


class CreateTablePlan(PlanNode):
    def __init__(self, node):
        self.node = node


class DropTablePlan(PlanNode):
    def __init__(self, table):
        self.table = table


class CreateIndexPlan(PlanNode):
    def __init__(self, node):
        self.node = node


class DropIndexPlan(PlanNode):
    def __init__(self, name, table):
        self.name  = name
        self.table = table


class AlterTablePlan(PlanNode):
    def __init__(self, node):
        self.node = node


class TruncatePlan(PlanNode):
    def __init__(self, table):
        self.table = table


class TxPlan(PlanNode):
    def __init__(self, operation, savepoint=None):
        self.operation = operation
        self.savepoint = savepoint


class ExplainPlan(PlanNode):
    def __init__(self, inner):
        self.inner = inner


class Planner:
    def __init__(self, catalog):
        self._catalog = catalog

    def plan(self, ast):
        if isinstance(ast, SelectNode):
            return self._plan_select(ast)
        if isinstance(ast, InsertNode):
            return InsertPlan(ast.table, ast.columns, ast.values)
        if isinstance(ast, UpdateNode):
            scan = self._plan_scan(ast.table, None, ast.where)
            return UpdatePlan(scan, ast.table, ast.assignments, ast.where)
        if isinstance(ast, DeleteNode):
            scan = self._plan_scan(ast.table, None, ast.where)
            return DeletePlan(scan, ast.table, ast.where)
        if isinstance(ast, CreateTableNode):
            return CreateTablePlan(ast)
        if isinstance(ast, DropTableNode):
            return DropTablePlan(ast.table)
        if isinstance(ast, CreateIndexNode):
            return CreateIndexPlan(ast)
        if isinstance(ast, DropIndexNode):
            return DropIndexPlan(ast.name, ast.table)
        if isinstance(ast, AlterTableNode):
            return AlterTablePlan(ast)
        if isinstance(ast, TruncateNode):
            return TruncatePlan(ast.table)
        if isinstance(ast, BeginNode):
            return TxPlan('BEGIN')
        if isinstance(ast, CommitNode):
            return TxPlan('COMMIT')
        if isinstance(ast, RollbackNode):
            return TxPlan('ROLLBACK', ast.savepoint)
        if isinstance(ast, SavepointNode):
            return TxPlan('SAVEPOINT', ast.name)
        if isinstance(ast, ExplainNode):
            return ExplainPlan(self.plan(ast.inner))
        raise ValueError(f"Cannot plan node type {type(ast).__name__}")

    def _plan_select(self, ast):
        table_name, alias = ast.from_table
        scan = self._plan_scan(table_name, alias, ast.where) if table_name else None

        for join in ast.joins:
            right_scan = self._plan_scan(join.table, join.alias, None)
            scan = NestedLoopJoin(scan, right_scan, join.condition, join.join_type)

        has_agg = self._has_aggregates(ast.columns)
        if has_agg or ast.group_by:
            scan = AggregateNode(scan, ast.group_by or [], ast.columns, ast.having)
            project = ProjectNode(scan, ast.columns)
        else:
            if ast.where and not isinstance(scan, (SeqScan, IndexScan)):
                scan = FilterNode(scan, ast.where)
            project = ProjectNode(scan, ast.columns)

        if ast.order_by:
            project = SortNode(project, ast.order_by)

        if ast.limit is not None or ast.offset is not None:
            project = LimitNode(project, ast.limit, ast.offset)

        return project

    def _plan_scan(self, table_name, alias, predicate):
        if table_name is None or isinstance(table_name, SubqueryNode):
            return SeqScan(table_name, alias, predicate)
        table_def = self._catalog.get_table(table_name)
        if table_def is None:
            return SeqScan(table_name, alias, predicate)
        index = self._try_index_scan(table_def, predicate)
        if index:
            col, op, val, idx_name = index
            return IndexScan(table_name, alias, idx_name, col, op, val)
        return SeqScan(table_name, alias, predicate)

    def _try_index_scan(self, table_def, predicate):
        if predicate is None:
            return None
        if not isinstance(predicate, BinaryOp):
            return None
        if predicate.op not in ('=', '<', '>', '<=', '>='):
            return None
        if isinstance(predicate.left, Column) and isinstance(predicate.right, Literal):
            col_name = predicate.left.name
            val      = predicate.right.value
        elif isinstance(predicate.right, Column) and isinstance(predicate.left, Literal):
            col_name = predicate.right.name
            val      = predicate.left.value
        else:
            return None
        for idx_name, idx in table_def.indexes.items():
            if idx.column_name == col_name:
                return col_name, predicate.op, val, idx_name
        return None

    def _has_aggregates(self, columns):
        AGG = {'COUNT', 'SUM', 'AVG', 'MIN', 'MAX'}
        def _check(node):
            if isinstance(node, FunctionCall) and node.name in AGG:
                return True
            if isinstance(node, BinaryOp):
                return _check(node.left) or _check(node.right)
            return False
        return any(_check(c) for c in columns)

    def describe(self, plan, indent=0):
        pad = '  ' * indent
        name = type(plan).__name__
        if isinstance(plan, SeqScan):
            return f"{pad}SeqScan({plan.table})"
        if isinstance(plan, IndexScan):
            return f"{pad}IndexScan({plan.table} via {plan.index_name} {plan.col}{plan.op}{plan.value})"
        if isinstance(plan, ProjectNode):
            return f"{pad}Project\n{self.describe(plan.child, indent+1)}"
        if isinstance(plan, FilterNode):
            return f"{pad}Filter\n{self.describe(plan.child, indent+1)}"
        if isinstance(plan, SortNode):
            return f"{pad}Sort\n{self.describe(plan.child, indent+1)}"
        if isinstance(plan, LimitNode):
            return f"{pad}Limit({plan.limit} offset {plan.offset})\n{self.describe(plan.child, indent+1)}"
        if isinstance(plan, AggregateNode):
            return f"{pad}Aggregate\n{self.describe(plan.child, indent+1)}"
        if isinstance(plan, NestedLoopJoin):
            return (f"{pad}NestedLoopJoin({plan.join_type})\n"
                    f"{self.describe(plan.left, indent+1)}\n"
                    f"{self.describe(plan.right, indent+1)}")
        return f"{pad}{name}"